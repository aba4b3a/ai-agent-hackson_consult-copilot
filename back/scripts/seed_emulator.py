"""Seed the local BigQuery emulator from app/storage_seed/companies/*/structured_knowledge.json.

The emulator has no persistent volume (see docker-compose.yaml), so all data
is lost whenever the `bigquery-emulator` container restarts. Re-run this
script any time that happens and the dashboard/knowledge-stats endpoints look
empty or fall back to sample data again.

Usage (from back/, with DRY_RUN=false and BIGQUERY_EMULATOR_HOST reachable):
    .venv/bin/python3 scripts/seed_emulator.py
or via docker compose:
    docker compose run --rm back python scripts/seed_emulator.py
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import settings
from app.services.bigquery_service import bigquery_service

SEED_ROOT = Path(__file__).resolve().parent.parent / "app" / "storage_seed" / "companies"


# The google-cloud-bigquery SDK submits DDL as an async job and polls
# jobs.getQueryResults for completion. Against this emulator that polling
# reliably hangs (job-insert retries alone take 5-10s, then .result() spins
# for minutes) whenever the emulator returns a 400 with reason
# "jobInternalError" — the SDK's job retry predicate treats that as
# transient and keeps retrying. The emulator's synchronous /queries REST
# endpoint returns the same result set instantly and doesn't go through that
# retry path, so DDL and data are issued directly against it here instead of
# through the SDK.
def _run_query(sql: str) -> dict:
    resp = requests.post(
        f"{settings.bigquery_emulator_host}/bigquery/v2/projects/{settings.project_id}/queries",
        json={"query": sql, "useLegacySql": False},
        timeout=10,
    )
    body = resp.json()
    if resp.status_code >= 400:
        raise RuntimeError(f"query failed ({resp.status_code}): {body}")
    return body


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _table_exists(dataset: str, table: str) -> bool:
    resp = requests.get(
        f"{settings.bigquery_emulator_host}/bigquery/v2/projects/{settings.project_id}"
        f"/datasets/{dataset}/tables/{table}",
        timeout=10,
    )
    return resp.status_code == 200


def _ensure_dataset(dataset: str) -> None:
    # `CREATE SCHEMA IF NOT EXISTS` via the query endpoint reports success but
    # doesn't reliably persist a brand-new dataset on this emulator; the
    # dedicated datasets.insert REST endpoint does.
    resp = requests.post(
        f"{settings.bigquery_emulator_host}/bigquery/v2/projects/{settings.project_id}/datasets",
        json={
            "datasetReference": {"projectId": settings.project_id, "datasetId": dataset},
            "location": settings.location,
        },
        timeout=10,
    )
    if resp.status_code >= 400 and "already created" not in resp.text:
        raise RuntimeError(f"dataset creation failed ({resp.status_code}): {resp.text}")


def _sql_literal(value: object) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, dict):
        escaped = json.dumps(value, ensure_ascii=False).replace("\\", "\\\\").replace("'", "\\'")
        return f"JSON '{escaped}'"
    if isinstance(value, list):
        return "[" + ", ".join(_sql_literal(v) for v in value) + "]"
    escaped = str(value).replace("\\", "\\\\").replace("'", "\\'")
    return f"'{escaped}'"


def _insert_rows(dataset: str, table: str, rows: list[dict]) -> int:
    # tabledata.insertAll (the SDK's insert_rows_json / streaming insert) has
    # a bug on this emulator build: it resolves the destination table by name
    # only, ignoring the dataset, so seeding two companies' `knowledge_nodes`
    # tables back to back silently clobbered the first company's data with
    # the second's. Plain DML INSERT via the query endpoint scopes correctly
    # by dataset, so rows are seeded that way instead.
    if not rows:
        return 0
    columns = list(rows[0].keys())
    values_sql = ",\n".join(
        "(" + ", ".join(_sql_literal(row[col]) for col in columns) + ")" for row in rows
    )
    sql = (
        f"INSERT INTO `{settings.project_id}.{dataset}.{table}` "
        f"({', '.join(columns)}) VALUES\n{values_sql}"
    )
    _run_query(sql)
    return len(rows)


def create_tables(company_id: str, dataset: str) -> None:
    # This emulator's DROP TABLE IF EXISTS still errors when the table is
    # absent (a real emulator bug), so only drop tables confirmed to exist,
    # keeping the script idempotent across re-runs.
    for table in ("survey_responses", "knowledge_nodes", "knowledge_edges"):
        prefixed = settings.company_table(company_id, table)
        if _table_exists(dataset, prefixed):
            _run_query(f"DROP TABLE `{settings.project_id}.{dataset}.{prefixed}`")

    ddl = bigquery_service.generate_core_tables_ddl(company_id)
    # PROPERTY GRAPH is only needed for the optional Notebook graph-query
    # feature, not for the dashboard/knowledge reads, and isn't supported by
    # this emulator, so it's dropped here rather than blocking table creation.
    graph_idx = ddl.ddl.find("CREATE OR REPLACE PROPERTY GRAPH")
    table_ddl = ddl.ddl[:graph_idx] if graph_idx != -1 else ddl.ddl

    _ensure_dataset(dataset)
    # generate_core_tables_ddl() leads with `CREATE SCHEMA IF NOT EXISTS`,
    # which - like above - doesn't reliably persist a brand-new dataset on
    # this emulator, so the schema statement is dropped in favor of
    # _ensure_dataset() and only the CREATE TABLE statements are run here.
    _, _, rest = table_ddl.partition(";")
    result = _run_query(rest)
    print(f"  tables: {result}")


def seed_nodes(company_id: str, dataset: str, nodes: list[dict]) -> None:
    rows = []
    for n in nodes:
        rows.append({
            "node_id": n["node_id"],
            "company_id": n.get("company_id", company_id),
            "node_type": n["node_type"],
            "label": n.get("label"),
            "description": n.get("description"),
            "source_response_id": n.get("source_response_id"),
            "confidence": n.get("confidence"),
            "valid_from": None,
            "valid_to": None,
            "status": n.get("status", "active"),
            "properties": n.get("properties") or {},
            "created_at": now_iso(),
            "updated_at": now_iso(),
        })
    inserted = _insert_rows(dataset, settings.company_table(company_id, "knowledge_nodes"), rows)
    print(f"  knowledge_nodes: {inserted}")


def seed_edges(company_id: str, dataset: str, edges: list[dict]) -> None:
    rows = []
    for e in edges:
        rows.append({
            "edge_id": e["edge_id"],
            "company_id": e.get("company_id", company_id),
            "source_node_id": e["source_node_id"],
            "target_node_id": e["target_node_id"],
            "edge_type": e["edge_type"],
            "description": e.get("description"),
            "source_response_id": e.get("source_response_id"),
            "confidence": e.get("confidence"),
            "strength": e.get("strength"),
            "observed_count": e.get("observed_count"),
            "properties": e.get("properties") or {},
            "created_at": now_iso(),
            "updated_at": now_iso(),
        })
    inserted = _insert_rows(dataset, settings.company_table(company_id, "knowledge_edges"), rows)
    print(f"  knowledge_edges: {inserted}")


def seed_responses(company_id: str, dataset: str, responses: list[dict]) -> None:
    rows = []
    for r in responses:
        rows.append({
            "response_id": r["response_id"],
            "company_id": r.get("company_id", company_id),
            "question_id": r.get("question_id"),
            "respondent_role": r.get("respondent_role"),
            "collected_at": r.get("collected_at"),
            "survey_frequency": r.get("survey_frequency"),
            "question_text": r.get("question_text"),
            "answer_type": r.get("answer_type"),
            "raw_answer": r.get("raw_answer"),
            "numeric_value": r.get("numeric_value"),
            "qualitative_summary": r.get("qualitative_summary"),
            "quantitative_summary": r.get("quantitative_summary"),
            "tags": r.get("tags") or [],
            "related_node_ids": r.get("related_node_ids") or [],
            "related_edge_ids": r.get("related_edge_ids") or [],
            "answer_json": r.get("answer_json") or {},
            "created_at": now_iso(),
        })
    inserted = _insert_rows(dataset, settings.company_table(company_id, "survey_responses"), rows)
    print(f"  survey_responses: {inserted}")


def main() -> None:
    for company_dir in sorted(SEED_ROOT.iterdir()):
        company_id = company_dir.name
        knowledge_file = company_dir / "structured_knowledge.json"
        if not knowledge_file.exists():
            continue
        print(f"== {company_id} ==")
        data = json.loads(knowledge_file.read_text(encoding="utf-8"))
        dataset = settings.dataset_id()

        create_tables(company_id, dataset)
        seed_nodes(company_id, dataset, data.get("knowledge_nodes", []))
        seed_edges(company_id, dataset, data.get("knowledge_edges", []))
        seed_responses(company_id, dataset, data.get("survey_responses", []))


if __name__ == "__main__":
    main()
