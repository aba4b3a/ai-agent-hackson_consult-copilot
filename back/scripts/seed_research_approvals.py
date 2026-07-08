"""Seed BigQuery with realistic Research/Approval data for the demo companies.

Research Inbox and Approvals were showing almost nothing because their
backing tables (``kpi_candidates``, ``focus_metric_candidates``,
``research_followup_question_events``, ``research_assignments``,
``approvals``) had never been populated for the sample companies. This script
derives that data from the existing
``app/storage_seed/companies/*/structured_knowledge.json`` fixtures (which
already contain realistic kpi_candidates/focus_metric_candidates/research_plan
content) and writes it into each company's BigQuery tenant dataset via the
same code paths the app uses at runtime (``research_service``,
``approval_service``).

Usage (from back/, with a production-pointed .env — PROJECT_ID and
GOOGLE_APPLICATION_CREDENTIALS already set, DRY_RUN=false):
    .venv/bin/python3 scripts/seed_research_approvals.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import settings
from app.crud.bigquery_crud import bigquery_crud
from app.schemas.approval import ApprovalCreate
from app.schemas.research import AssignmentCreate, FollowupQuestionCreate
from app.services.approval_service import approval_service
from app.services.research_service import research_service
from app.utils.bigquery_sql import sql_literal
from app.utils.time import utc_now_iso

SEED_ROOT = Path(__file__).resolve().parent.parent / "app" / "storage_seed" / "companies"

ROLE_MAP = {
    "経営者": "owner",
    "管理者": "manager",
    "バックオフィス": "manager",
    "営業担当": "sales",
    "営業": "sales",
    "現場担当者": "staff",
    "現場": "staff",
    "店長・販売スタッフ": "staff",
}


def _map_role(raw: str) -> str:
    return ROLE_MAP.get(raw, "staff")


def _tenant_dataset(company_id: str) -> str:
    safe = company_id.replace("-", "_").replace(".", "_")
    return f"cd_tenant_{safe}"


def _ensure_candidate_tables(dataset: str) -> None:
    ddl = f"""
CREATE SCHEMA IF NOT EXISTS `{settings.project_id}.{dataset}`;

CREATE TABLE IF NOT EXISTS `{settings.project_id}.{dataset}.kpi_candidates` (
  kpi_candidate_id STRING NOT NULL,
  company_id STRING NOT NULL,
  common_kpi_id STRING,
  kpi_name STRING NOT NULL,
  kpi_domain STRING,
  kpi_type STRING,
  description STRING,
  calculation_hint STRING,
  data_source_hint STRING,
  measurement_frequency STRING,
  reason STRING,
  source_answer_event_ids ARRAY<STRING>,
  source_followup_answer_event_ids ARRAY<STRING>,
  source_gcs_uris ARRAY<STRING>,
  confidence FLOAT64,
  importance_score FLOAT64,
  approval_status STRING,
  approved_by STRING,
  approved_at TIMESTAMP,
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS `{settings.project_id}.{dataset}.focus_metric_candidates` (
  focus_metric_candidate_id STRING NOT NULL,
  company_id STRING NOT NULL,
  metric_name STRING NOT NULL,
  metric_category STRING,
  description STRING,
  related_kpi_candidate_ids ARRAY<STRING>,
  related_common_kpi_ids ARRAY<STRING>,
  observation_signal_types ARRAY<STRING>,
  calculation_hint STRING,
  data_source_hint STRING,
  measurement_frequency STRING,
  trigger_condition STRING,
  followup_policy STRING,
  reason STRING,
  source_answer_event_ids ARRAY<STRING>,
  source_followup_answer_event_ids ARRAY<STRING>,
  source_gcs_uris ARRAY<STRING>,
  confidence FLOAT64,
  priority_score FLOAT64,
  approval_status STRING,
  approved_by STRING,
  approved_at TIMESTAMP,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);
""".strip()
    bigquery_crud.execute_sql(ddl)


def _insert_row(table: str, row: dict) -> None:
    columns = list(row.keys())
    values_sql = ", ".join(sql_literal(row[column]) for column in columns)
    sql = f"INSERT INTO `{table}` ({', '.join(columns)}) VALUES ({values_sql})"
    bigquery_crud.execute_sql(sql)


def seed_company(company_id: str, data: dict) -> None:
    print(f"== {company_id} ==")
    dataset = _tenant_dataset(company_id)
    _ensure_candidate_tables(dataset)
    now = utc_now_iso()

    kpi_candidates = data.get("kpi_candidates", [])
    focus_candidates = data.get("focus_metric_candidates", [])
    research_plan = data.get("research_plan", [])

    kpi_table = f"{settings.project_id}.{dataset}.kpi_candidates"
    for kpi in kpi_candidates:
        _insert_row(kpi_table, {
            "kpi_candidate_id": kpi["kpi_candidate_id"],
            "company_id": company_id,
            "common_kpi_id": None,
            "kpi_name": kpi["kpi_name"],
            "kpi_domain": kpi.get("kpi_domain"),
            "kpi_type": kpi.get("kpi_type"),
            "description": kpi.get("description", ""),
            "calculation_hint": kpi.get("calculation_hint"),
            "data_source_hint": kpi.get("data_source_hint"),
            "measurement_frequency": kpi.get("measurement_frequency"),
            "reason": kpi.get("description", ""),
            "source_answer_event_ids": kpi.get("source_refs", []),
            "source_followup_answer_event_ids": [],
            "source_gcs_uris": [],
            "confidence": float(kpi.get("confidence", 0.0)),
            "importance_score": float(kpi.get("confidence", 0.0)),
            "approval_status": kpi.get("approval_status", "proposed"),
            "approved_by": None,
            "approved_at": None,
            "created_at": now,
            "updated_at": now,
        })
    print(f"  kpi_candidates: {len(kpi_candidates)}")

    focus_table = f"{settings.project_id}.{dataset}.focus_metric_candidates"
    for metric in focus_candidates:
        _insert_row(focus_table, {
            "focus_metric_candidate_id": metric["focus_metric_candidate_id"],
            "company_id": company_id,
            "metric_name": metric["metric_name"],
            "metric_category": metric.get("metric_category"),
            "description": metric.get("description", ""),
            "related_kpi_candidate_ids": metric.get("related_kpi_candidate_ids", []),
            "related_common_kpi_ids": [],
            "observation_signal_types": metric.get("observation_signal_types", []),
            "calculation_hint": None,
            "data_source_hint": None,
            "measurement_frequency": metric.get("measurement_frequency"),
            "trigger_condition": metric.get("trigger_condition"),
            "followup_policy": metric.get("followup_policy"),
            "reason": metric.get("description", ""),
            "source_answer_event_ids": metric.get("source_refs", []),
            "source_followup_answer_event_ids": [],
            "source_gcs_uris": [],
            "confidence": float(metric.get("confidence", 0.0)),
            "priority_score": float(metric.get("confidence", 0.0)),
            "approval_status": metric.get("approval_status", "proposed"),
            "approved_by": None,
            "approved_at": None,
            "created_at": now,
            "updated_at": now,
        })
    print(f"  focus_metric_candidates: {len(focus_candidates)}")

    question_count = 0
    assignment_count = 0
    for task in research_plan:
        role = _map_role(task.get("target_role", ""))
        for index, question_text in enumerate(task.get("base_questions", [])):
            followup_question_id = f"fq_{task['research_task_id']}_{index + 1}"
            research_service.register_followup_question(
                FollowupQuestionCreate(
                    company_id=company_id,
                    followup_question_id=followup_question_id,
                    question_text=question_text,
                    question_category=task.get("question_intent"),
                    target_role=role,
                    reason=task.get("followup_policy"),
                    related_kpi_candidates=task.get("related_kpi_candidates", []),
                    related_focus_metric_candidates=task.get(
                        "related_focus_metric_candidates", []
                    ),
                    expected_answer_format="free_text",
                    priority_score=0.7,
                    source_answer_event_ids=[],
                )
            )
            question_count += 1
            research_service.assign(
                AssignmentCreate(
                    company_id=company_id,
                    followup_question_id=followup_question_id,
                    target_role=role,
                    target_user_id=None,
                    expected_response_by=None,
                )
            )
            assignment_count += 1
    print(f"  research_followup_question_events: {question_count}, research_assignments: {assignment_count}")

    approval_count = 0
    for kpi in kpi_candidates:
        approval_service.create(
            ApprovalCreate(
                company_id=company_id,
                target_type="kpi_candidate",
                target_id=kpi["kpi_candidate_id"],
                title=kpi["kpi_name"],
                summary=kpi.get("description", ""),
                proposed_payload=kpi,
                confidence=kpi.get("confidence"),
                reason=kpi.get("calculation_hint"),
                created_by="agent:knowledge_agent",
            )
        )
        approval_count += 1
    for metric in focus_candidates:
        approval_service.create(
            ApprovalCreate(
                company_id=company_id,
                target_type="focus_metric_candidate",
                target_id=metric["focus_metric_candidate_id"],
                title=metric["metric_name"],
                summary=metric.get("description", ""),
                proposed_payload=metric,
                confidence=metric.get("confidence"),
                reason=metric.get("trigger_condition"),
                created_by="agent:knowledge_agent",
            )
        )
        approval_count += 1
    print(f"  approvals: {approval_count}")


def main() -> None:
    if settings.dry_run:
        print("DRY_RUN=true — nothing will be written. Set DRY_RUN=false to seed real BigQuery data.")
        return
    for company_dir in sorted(SEED_ROOT.iterdir()):
        knowledge_file = company_dir / "structured_knowledge.json"
        if not knowledge_file.exists():
            continue
        data = json.loads(knowledge_file.read_text(encoding="utf-8"))
        seed_company(company_dir.name, data)


if __name__ == "__main__":
    main()
