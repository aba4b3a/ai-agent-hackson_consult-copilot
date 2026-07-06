from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from google.cloud import bigquery
from agents.config import settings


def _client() -> bigquery.Client:
    """Create a BigQuery client configured for local or production environment."""
    if settings.app_env == 'local' and settings.bigquery_emulator_host:
        # Use BigQuery emulator for local development
        os.environ['BIGQUERY_EMULATOR_HOST'] = settings.bigquery_emulator_host
        return bigquery.Client(project=settings.project_id, location=settings.location)
    else:
        # Use Google Cloud BigQuery for production
        return bigquery.Client(project=settings.project_id)


def _sql_string(value: str | None) -> str:
    if value is None:
        return "NULL"
    return "'" + value.replace("'", "''") + "'"


def _sql_string_array(values: list[str] | None) -> str:
    if not values:
        return "ARRAY<STRING>[]"
    return "[" + ", ".join(_sql_string(str(value)) for value in values) + "]"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _tenant_dataset(company_id: str) -> str:
    return f"{settings.project_id}.{tenant_dataset_id(company_id)}"


def _insert_json_rows(table: str, rows: list[dict]) -> dict:
    if not rows:
        return {"skipped": True, "reason": "no rows", "table": table}
    if settings.dry_run:
        return {"dry_run": True, "table": table, "rows": rows}
    client = _client()
    errors = client.insert_rows_json(table, rows)
    if errors:
        raise RuntimeError(json.dumps(errors, ensure_ascii=False))
    return {"dry_run": False, "table": table, "inserted": len(rows)}


def _json_value(value: object) -> str:
    return json.dumps(value if value is not None else {}, ensure_ascii=False)


def _source_refs_to_columns(record: dict) -> dict:
    source_refs = record.get("source_refs") or []
    answer_ids = record.get("source_answer_event_ids") or [
        ref.removeprefix("answer_event_id:")
        for ref in source_refs
        if str(ref).startswith("answer_event_id:")
    ]
    followup_ids = record.get("source_followup_answer_event_ids") or [
        ref.removeprefix("followup_answer_event_id:")
        for ref in source_refs
        if str(ref).startswith("followup_answer_event_id:")
    ]
    gcs_uris = record.get("source_gcs_uris") or [
        ref for ref in source_refs if str(ref).startswith("gs://")
    ]
    return {
        "source_answer_event_ids": answer_ids,
        "source_followup_answer_event_ids": followup_ids,
        "source_gcs_uris": gcs_uris,
    }


def create_company_dataset(company_id: str) -> dict:
    dataset_id = settings.dataset_id(company_id)
    full_dataset_id = f"{settings.project_id}.{dataset_id}"
    if settings.dry_run:
        return {"dry_run": True, "dataset": full_dataset_id}
    client = _client()
    dataset = bigquery.Dataset(full_dataset_id)
    dataset.location = settings.location
    client.create_dataset(dataset, exists_ok=True)
    return {"dry_run": False, "dataset": full_dataset_id}


def common_dataset_id() -> str:
    return os.getenv("BQ_COMMON_DATASET", "cd_common")


def tenant_dataset_id(company_id: str) -> str:
    safe_company_id = company_id.replace("-", "_").replace(".", "_")
    prefix = os.getenv("BQ_TENANT_DATASET_PREFIX", "cd_tenant")
    return f"{prefix}_{safe_company_id}"


def generate_common_tables_ddl() -> dict:
    dataset = common_dataset_id()
    ddl = f"""
CREATE SCHEMA IF NOT EXISTS `{settings.project_id}.{dataset}`
OPTIONS(location="{settings.location}");

CREATE TABLE IF NOT EXISTS `{settings.project_id}.{dataset}.companies` (
  company_id STRING NOT NULL,
  company_name STRING NOT NULL,
  legal_name STRING,
  industry_code STRING,
  industry_name STRING,
  sub_industry_code STRING,
  sub_industry_name STRING,
  business_type STRING,
  company_size_segment STRING,
  employee_count INT64,
  annual_revenue_range STRING,
  region_country STRING,
  region_prefecture STRING,
  region_city STRING,
  primary_sales_channels ARRAY<STRING>,
  primary_customer_types ARRAY<STRING>,
  primary_revenue_models ARRAY<STRING>,
  onboarding_status STRING,
  active_status STRING,
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP
)
CLUSTER BY company_id, industry_code, company_size_segment;

CREATE TABLE IF NOT EXISTS `{settings.project_id}.{dataset}.company_dataset_registry` (
  company_id STRING NOT NULL,
  dataset_project_id STRING NOT NULL,
  dataset_id STRING NOT NULL,
  dataset_region STRING NOT NULL,
  schema_version STRING,
  dataset_status STRING,
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP
)
CLUSTER BY company_id, dataset_status;

CREATE TABLE IF NOT EXISTS `{settings.project_id}.{dataset}.schema_migration_history` (
  migration_id STRING NOT NULL,
  target_scope STRING NOT NULL,
  target_dataset STRING NOT NULL,
  version STRING NOT NULL,
  migration_name STRING NOT NULL,
  checksum STRING NOT NULL,
  applied_at TIMESTAMP NOT NULL,
  applied_by STRING,
  status STRING,
  error_message STRING
)
CLUSTER BY target_scope, target_dataset, version;

CREATE TABLE IF NOT EXISTS `{settings.project_id}.{dataset}.onboarding_question_master` (
  question_id STRING NOT NULL,
  version STRING NOT NULL,
  question_order INT64 NOT NULL,
  question_text STRING NOT NULL,
  question_category STRING NOT NULL,
  answer_type STRING NOT NULL,
  purpose STRING,
  related_kpi_domains ARRAY<STRING>,
  related_focus_metric_categories ARRAY<STRING>,
  is_required BOOL NOT NULL,
  is_active BOOL NOT NULL,
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP
)
CLUSTER BY version, question_category;

CREATE TABLE IF NOT EXISTS `{settings.project_id}.{dataset}.common_kpi_master` (
  common_kpi_id STRING NOT NULL,
  kpi_name STRING NOT NULL,
  kpi_domain STRING NOT NULL,
  kpi_type STRING,
  description STRING,
  standard_calculation_formula STRING,
  standard_unit STRING,
  recommended_frequency STRING,
  applicable_industry_codes ARRAY<STRING>,
  applicable_business_types ARRAY<STRING>,
  is_active BOOL NOT NULL,
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP
)
CLUSTER BY kpi_domain, kpi_type;
""".strip()
    return {"dataset": f"{settings.project_id}.{dataset}", "ddl": ddl}


def generate_tenant_tables_ddl(company_id: str) -> dict:
    dataset = tenant_dataset_id(company_id)
    tenant = f"{settings.project_id}.{dataset}"
    ddl = f"""
CREATE SCHEMA IF NOT EXISTS `{tenant}`
OPTIONS(location="{settings.location}");

CREATE TABLE IF NOT EXISTS `{tenant}.onboarding_answer_events` (
  answer_event_id STRING NOT NULL,
  company_id STRING NOT NULL,
  question_id STRING NOT NULL,
  question_version STRING NOT NULL,
  question_text STRING,
  respondent_role STRING,
  answered_at TIMESTAMP NOT NULL,
  answer_text STRING,
  answer_payload JSON,
  extracted_summary STRING,
  extracted_entities JSON,
  extracted_signals JSON,
  source_gcs_uri STRING,
  source_file_generation STRING,
  created_at TIMESTAMP NOT NULL
)
PARTITION BY DATE(answered_at)
CLUSTER BY company_id, question_id;

CREATE TABLE IF NOT EXISTS `{tenant}.research_followup_question_events` (
  followup_question_id STRING NOT NULL,
  company_id STRING NOT NULL,
  generated_at TIMESTAMP NOT NULL,
  question_text STRING NOT NULL,
  question_category STRING,
  target_role STRING,
  reason STRING,
  related_kpi_candidates ARRAY<STRING>,
  related_focus_metric_candidates ARRAY<STRING>,
  expected_answer_format STRING,
  priority_score FLOAT64,
  status STRING,
  source_answer_event_ids ARRAY<STRING>,
  source_gcs_uri STRING,
  created_at TIMESTAMP NOT NULL
)
PARTITION BY DATE(generated_at)
CLUSTER BY company_id, status, question_category;

CREATE TABLE IF NOT EXISTS `{tenant}.followup_answer_events` (
  followup_answer_event_id STRING NOT NULL,
  company_id STRING NOT NULL,
  followup_question_id STRING NOT NULL,
  question_text STRING,
  respondent_role STRING,
  answered_at TIMESTAMP NOT NULL,
  answer_text STRING,
  answer_payload JSON,
  extracted_summary STRING,
  extracted_entities JSON,
  extracted_signals JSON,
  source_gcs_uri STRING,
  source_file_generation STRING,
  created_at TIMESTAMP NOT NULL
)
PARTITION BY DATE(answered_at)
CLUSTER BY company_id, followup_question_id;

CREATE TABLE IF NOT EXISTS `{tenant}.kpi_candidates` (
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
)
CLUSTER BY company_id, kpi_domain, approval_status;

CREATE TABLE IF NOT EXISTS `{tenant}.focus_metric_candidates` (
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
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP
)
CLUSTER BY company_id, metric_category, approval_status;

CREATE TABLE IF NOT EXISTS `{tenant}.current_kpi_definitions` (
  kpi_id STRING NOT NULL,
  company_id STRING NOT NULL,
  common_kpi_id STRING,
  kpi_name STRING NOT NULL,
  kpi_domain STRING,
  kpi_type STRING,
  description STRING,
  calculation_formula STRING,
  unit STRING,
  measurement_frequency STRING,
  data_source_type STRING,
  data_source_detail STRING,
  status STRING,
  source_kpi_candidate_id STRING,
  source_wiki_uri STRING,
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP
)
CLUSTER BY company_id, status, kpi_domain;

CREATE TABLE IF NOT EXISTS `{tenant}.observation_signals` (
  observation_signal_id STRING NOT NULL,
  company_id STRING NOT NULL,
  signal_name STRING NOT NULL,
  signal_category STRING,
  description STRING,
  related_focus_metric_candidate_ids ARRAY<STRING>,
  related_kpi_candidate_ids ARRAY<STRING>,
  detection_rule STRING,
  expected_source STRING,
  expected_frequency STRING,
  severity STRING,
  reason STRING,
  source_answer_event_ids ARRAY<STRING>,
  source_followup_answer_event_ids ARRAY<STRING>,
  source_gcs_uris ARRAY<STRING>,
  confidence FLOAT64,
  approval_status STRING,
  approved_by STRING,
  approved_at TIMESTAMP,
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP
)
CLUSTER BY company_id, signal_category, approval_status;

CREATE TABLE IF NOT EXISTS `{tenant}.current_focus_metric_definitions` (
  focus_metric_id STRING NOT NULL,
  company_id STRING NOT NULL,
  metric_name STRING NOT NULL,
  metric_category STRING,
  description STRING,
  related_kpi_ids ARRAY<STRING>,
  related_common_kpi_ids ARRAY<STRING>,
  observation_signal_types ARRAY<STRING>,
  calculation_method STRING,
  unit STRING,
  measurement_frequency STRING,
  trigger_condition STRING,
  followup_policy STRING,
  status STRING,
  source_focus_metric_candidate_id STRING,
  source_wiki_uri STRING,
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP
)
CLUSTER BY company_id, status, metric_category;
""".strip()
    return {"company_id": company_id, "dataset": tenant, "ddl": ddl}


def create_common_tables() -> dict:
    ddl_result = generate_common_tables_ddl()
    execution = execute_sql(ddl_result["ddl"])
    return {"ddl": ddl_result, "execution": execution}


def create_tenant_tables(company_id: str) -> dict:
    ddl_result = generate_tenant_tables_ddl(company_id)
    execution = execute_sql(ddl_result["ddl"])
    return {"company_id": company_id, "ddl": ddl_result, "execution": execution}


def generate_core_tables_ddl(company_id: str) -> dict:
    dataset = settings.dataset_id(company_id)
    project = settings.project_id
    graph_name = settings.bq_graph_name
    ddl = f'''
CREATE SCHEMA IF NOT EXISTS `{project}.{dataset}`
OPTIONS(location="{settings.location}");

CREATE OR REPLACE TABLE `{project}.{dataset}.survey_responses` (
  response_id STRING NOT NULL,
  company_id STRING NOT NULL,
  question_id STRING,
  respondent_role STRING,
  collected_at TIMESTAMP,
  survey_frequency STRING,
  question_text STRING,
  answer_type STRING,
  raw_answer STRING,
  numeric_value FLOAT64,
  qualitative_summary STRING,
  quantitative_summary STRING,
  tags ARRAY<STRING>,
  related_node_ids ARRAY<STRING>,
  related_edge_ids ARRAY<STRING>,
  answer_json JSON,
  created_at TIMESTAMP,
  PRIMARY KEY (response_id) NOT ENFORCED
);

CREATE OR REPLACE TABLE `{project}.{dataset}.knowledge_nodes` (
  node_id STRING NOT NULL,
  company_id STRING NOT NULL,
  node_type STRING NOT NULL,
  label STRING,
  description STRING,
  source_response_id STRING,
  confidence FLOAT64,
  valid_from TIMESTAMP,
  valid_to TIMESTAMP,
  status STRING,
  properties JSON,
  created_at TIMESTAMP,
  updated_at TIMESTAMP,
  PRIMARY KEY (node_id) NOT ENFORCED
);

CREATE OR REPLACE TABLE `{project}.{dataset}.knowledge_edges` (
  edge_id STRING NOT NULL,
  company_id STRING NOT NULL,
  source_node_id STRING NOT NULL,
  target_node_id STRING NOT NULL,
  edge_type STRING NOT NULL,
  description STRING,
  source_response_id STRING,
  confidence FLOAT64,
  strength FLOAT64,
  observed_count INT64,
  properties JSON,
  created_at TIMESTAMP,
  updated_at TIMESTAMP,
  PRIMARY KEY (edge_id) NOT ENFORCED,
  FOREIGN KEY (source_node_id) REFERENCES `{project}.{dataset}.knowledge_nodes`(node_id) NOT ENFORCED,
  FOREIGN KEY (target_node_id) REFERENCES `{project}.{dataset}.knowledge_nodes`(node_id) NOT ENFORCED
);

CREATE OR REPLACE PROPERTY GRAPH `{project}.{dataset}.{graph_name}`
NODE TABLES (
  `{project}.{dataset}.knowledge_nodes`
    KEY (node_id)
    LABEL KnowledgeNode
    PROPERTIES (company_id, node_type, label, description, confidence, status, properties)
)
EDGE TABLES (
  `{project}.{dataset}.knowledge_edges`
    SOURCE KEY (source_node_id) REFERENCES knowledge_nodes (node_id)
    DESTINATION KEY (target_node_id) REFERENCES knowledge_nodes (node_id)
    LABEL KnowledgeEdge
    PROPERTIES (company_id, edge_type, description, confidence, strength, observed_count, properties)
);
'''.strip()
    return {"company_id": company_id, "dataset": f"{project}.{dataset}", "graph": f"{project}.{dataset}.{graph_name}", "ddl": ddl}


def execute_sql(sql: str) -> dict:
    if settings.dry_run:
        return {"dry_run": True, "sql": sql}
    client = _client()
    job = client.query(sql)
    job.result()
    return {"dry_run": False, "job_id": job.job_id}


def create_core_tables(company_id: str) -> dict:
    ddl_result = generate_core_tables_ddl(company_id)
    execution = execute_sql(ddl_result["ddl"])
    return {"company_id": company_id, "ddl": ddl_result, "execution": execution}


def insert_survey_response(
    company_id: str,
    response_id: str,
    question_id: str,
    respondent_role: str,
    collected_at: str,
    survey_frequency: str,
    question_text: str,
    answer_type: str,
    raw_answer: str,
    numeric_value: float | None = None,
    qualitative_summary: str | None = None,
    quantitative_summary: str | None = None,
    tags: list[str] | None = None,
    related_node_ids: list[str] | None = None,
    related_edge_ids: list[str] | None = None,
    answer_json: dict | None = None,
) -> dict:
    dataset = settings.dataset_id(company_id)
    table = f"{settings.project_id}.{dataset}.survey_responses"
    row = {
        "response_id": response_id,
        "company_id": company_id,
        "question_id": question_id,
        "respondent_role": respondent_role,
        "collected_at": collected_at,
        "survey_frequency": survey_frequency,
        "question_text": question_text,
        "answer_type": answer_type,
        "raw_answer": raw_answer,
        "numeric_value": numeric_value,
        "qualitative_summary": qualitative_summary,
        "quantitative_summary": quantitative_summary,
        "tags": tags or [],
        "related_node_ids": related_node_ids or [],
        "related_edge_ids": related_edge_ids or [],
        "answer_json": answer_json or {},
        "created_at": collected_at,
    }
    if settings.dry_run:
        return {"dry_run": True, "table": table, "row": row}
    client = _client()
    errors = client.insert_rows_json(table, [row])
    if errors:
        raise RuntimeError(json.dumps(errors, ensure_ascii=False))
    return {"dry_run": False, "table": table, "inserted": 1}


def insert_onboarding_answer_events(company_id: str, records: list[dict]) -> dict:
    """Insert initial 18-question answer events into the tenant table."""
    table = f"{_tenant_dataset(company_id)}.onboarding_answer_events"
    now = _now_iso()
    rows = []
    for record in records:
        rows.append(
            {
                "answer_event_id": record["answer_event_id"],
                "company_id": company_id,
                "question_id": record["question_id"],
                "question_version": record.get("question_version", "v1"),
                "question_text": record.get("question_text"),
                "respondent_role": record.get("respondent_role"),
                "answered_at": record.get("answered_at", now),
                "answer_text": record.get("answer_text"),
                "answer_payload": record.get("answer_payload", {}),
                "extracted_summary": record.get("extracted_summary"),
                "extracted_entities": record.get("extracted_entities", {}),
                "extracted_signals": record.get("extracted_signals", {}),
                "source_gcs_uri": record.get("source_gcs_uri"),
                "source_file_generation": record.get("source_file_generation"),
                "created_at": record.get("created_at", now),
            }
        )
    return _insert_json_rows(table, rows)


def insert_kpi_candidates(company_id: str, records: list[dict]) -> dict:
    """Insert proposed KPI candidates. This never publishes current KPI definitions."""
    table = f"{_tenant_dataset(company_id)}.kpi_candidates"
    now = _now_iso()
    rows = []
    for record in records:
        source_columns = _source_refs_to_columns(record)
        rows.append(
            {
                "kpi_candidate_id": record["kpi_candidate_id"],
                "company_id": company_id,
                "common_kpi_id": record.get("common_kpi_id"),
                "kpi_name": record["kpi_name"],
                "kpi_domain": record.get("kpi_domain"),
                "kpi_type": record.get("kpi_type"),
                "description": record.get("description", ""),
                "calculation_hint": record.get("calculation_hint"),
                "data_source_hint": record.get("data_source_hint"),
                "measurement_frequency": record.get("measurement_frequency"),
                "reason": record.get("reason", ""),
                "source_answer_event_ids": source_columns["source_answer_event_ids"],
                "source_followup_answer_event_ids": source_columns[
                    "source_followup_answer_event_ids"
                ],
                "source_gcs_uris": source_columns["source_gcs_uris"],
                "confidence": float(record.get("confidence", 0.0)),
                "importance_score": float(record.get("importance_score", 0.0)),
                "approval_status": record.get("approval_status", "proposed"),
                "approved_by": record.get("approved_by"),
                "approved_at": record.get("approved_at"),
                "created_at": record.get("created_at", now),
                "updated_at": record.get("updated_at", now),
            }
        )
    return _insert_json_rows(table, rows)


def insert_focus_metric_candidates(company_id: str, records: list[dict]) -> dict:
    """Insert proposed focus metric candidates. This never publishes current definitions."""
    table = f"{_tenant_dataset(company_id)}.focus_metric_candidates"
    now = _now_iso()
    rows = []
    for record in records:
        source_columns = _source_refs_to_columns(record)
        rows.append(
            {
                "focus_metric_candidate_id": record["focus_metric_candidate_id"],
                "company_id": company_id,
                "metric_name": record["metric_name"],
                "metric_category": record.get("metric_category"),
                "description": record.get("description", ""),
                "related_kpi_candidate_ids": record.get("related_kpi_candidate_ids")
                or record.get("related_kpi_candidates")
                or [],
                "related_common_kpi_ids": record.get("related_common_kpi_ids", []),
                "observation_signal_types": record.get("observation_signal_types", []),
                "calculation_hint": record.get("calculation_hint"),
                "data_source_hint": record.get("data_source_hint"),
                "measurement_frequency": record.get("measurement_frequency"),
                "trigger_condition": record.get("trigger_condition"),
                "followup_policy": record.get("followup_policy"),
                "reason": record.get("reason", ""),
                "source_answer_event_ids": source_columns["source_answer_event_ids"],
                "source_followup_answer_event_ids": source_columns[
                    "source_followup_answer_event_ids"
                ],
                "source_gcs_uris": source_columns["source_gcs_uris"],
                "confidence": float(record.get("confidence", 0.0)),
                "priority_score": float(record.get("priority_score", 0.0)),
                "approval_status": record.get("approval_status", "proposed"),
                "approved_by": record.get("approved_by"),
                "approved_at": record.get("approved_at"),
                "created_at": record.get("created_at", now),
                "updated_at": record.get("updated_at", now),
            }
        )
    return _insert_json_rows(table, rows)


def insert_observation_signals(company_id: str, records: list[dict]) -> dict:
    """Insert proposed observation signals. Approval to a signal is recorded
    via the back HITL pipeline (approval_status remains 'proposed' here)."""
    table = f"{_tenant_dataset(company_id)}.observation_signals"
    now = _now_iso()
    rows = []
    for record in records:
        source_columns = _source_refs_to_columns(record)
        rows.append(
            {
                "observation_signal_id": record["observation_signal_id"],
                "company_id": company_id,
                "signal_name": record["signal_name"],
                "signal_category": record.get("signal_category"),
                "description": record.get("description", ""),
                "related_focus_metric_candidate_ids": record.get(
                    "related_focus_metric_candidate_ids", []
                ),
                "related_kpi_candidate_ids": record.get("related_kpi_candidate_ids", []),
                "detection_rule": record.get("detection_rule"),
                "expected_source": record.get("expected_source"),
                "expected_frequency": record.get("expected_frequency"),
                "severity": record.get("severity"),
                "reason": record.get("reason", ""),
                "source_answer_event_ids": source_columns["source_answer_event_ids"],
                "source_followup_answer_event_ids": source_columns[
                    "source_followup_answer_event_ids"
                ],
                "source_gcs_uris": source_columns["source_gcs_uris"],
                "confidence": float(record.get("confidence", 0.0)),
                "approval_status": record.get("approval_status", "proposed"),
                "approved_by": record.get("approved_by"),
                "approved_at": record.get("approved_at"),
                "created_at": record.get("created_at", now),
                "updated_at": record.get("updated_at", now),
            }
        )
    return _insert_json_rows(table, rows)


def insert_research_followup_question_events(company_id: str, records: list[dict]) -> dict:
    """Insert follow-up questions generated from a research plan."""
    table = f"{_tenant_dataset(company_id)}.research_followup_question_events"
    now = _now_iso()
    rows = []
    for record in records:
        rows.append(
            {
                "followup_question_id": record["followup_question_id"],
                "company_id": company_id,
                "generated_at": record.get("generated_at", now),
                "question_text": record["question_text"],
                "question_category": record.get("question_category"),
                "target_role": record.get("target_role"),
                "reason": record.get("reason"),
                "related_kpi_candidates": record.get("related_kpi_candidates", []),
                "related_focus_metric_candidates": record.get(
                    "related_focus_metric_candidates", []
                ),
                "expected_answer_format": record.get("expected_answer_format"),
                "priority_score": float(record.get("priority_score", 0.0)),
                "status": record.get("status", "proposed"),
                "source_answer_event_ids": record.get("source_answer_event_ids", []),
                "source_gcs_uri": record.get("source_gcs_uri"),
                "created_at": record.get("created_at", now),
            }
        )
    return _insert_json_rows(table, rows)


def insert_wiki_revision_log(company_id: str, records: list[dict]) -> dict:
    """Return a safe revision-log write plan.

    The starter DDL does not define a wiki revision table yet, so this tool is
    intentionally plan-only in dry-run mode and explicit about the missing DDL.
    """
    return {
        "company_id": company_id,
        "operation": "insert_wiki_revision_log",
        "records": records,
        "requires_human_review": False,
        "note": "No wiki_revision_log table exists in the bundled DDL; persist the files in Cloud Storage and add DDL before enabling this write.",
    }


def upsert_knowledge_nodes(company_id: str, nodes: list[dict]) -> dict:
    if not nodes:
        return {"skipped": True, "reason": "no nodes"}
    required_keys = ("node_id", "node_type")
    valid_nodes = [node for node in nodes if all(node.get(key) for key in required_keys)]
    invalid_count = len(nodes) - len(valid_nodes)
    if not valid_nodes:
        return {
            "skipped": True,
            "reason": f"all {len(nodes)} node(s) missing required field(s) {required_keys}",
        }
    dataset = settings.dataset_id(company_id)
    table = f"`{settings.project_id}.{dataset}.knowledge_nodes`"
    rows_sql = []
    for node in valid_nodes:
        rows_sql.append(f'''
SELECT
  {_sql_string(node["node_id"])} AS node_id,
  {_sql_string(company_id)} AS company_id,
  {_sql_string(node["node_type"])} AS node_type,
  {_sql_string(node.get("label", ""))} AS label,
  {_sql_string(node.get("description", ""))} AS description,
  {_sql_string(node.get("source_response_id"))} AS source_response_id,
  {float(node.get("confidence", 0.5))} AS confidence,
  CURRENT_TIMESTAMP() AS valid_from,
  NULL AS valid_to,
  'active' AS status,
  PARSE_JSON(''' + _sql_string(json.dumps(node.get("properties", {}), ensure_ascii=False)) + f''') AS properties,
  CURRENT_TIMESTAMP() AS created_at,
  CURRENT_TIMESTAMP() AS updated_at
''')
    sql = f'''
MERGE {table} T
USING ({" UNION ALL ".join(rows_sql)}) S
ON T.node_id = S.node_id
WHEN MATCHED THEN UPDATE SET
  node_type = S.node_type,
  label = S.label,
  description = S.description,
  confidence = S.confidence,
  properties = S.properties,
  updated_at = CURRENT_TIMESTAMP()
WHEN NOT MATCHED THEN INSERT ROW
'''.strip()
    result = execute_sql(sql)
    if invalid_count:
        result["skipped_invalid_count"] = invalid_count
    return result


def upsert_knowledge_edges(company_id: str, edges: list[dict]) -> dict:
    if not edges:
        return {"skipped": True, "reason": "no edges"}
    required_keys = ("edge_id", "source_node_id", "target_node_id", "edge_type")
    valid_edges = [edge for edge in edges if all(edge.get(key) for key in required_keys)]
    invalid_count = len(edges) - len(valid_edges)
    if not valid_edges:
        return {
            "skipped": True,
            "reason": f"all {len(edges)} edge(s) missing required field(s) {required_keys}",
        }
    dataset = settings.dataset_id(company_id)
    table = f"`{settings.project_id}.{dataset}.knowledge_edges`"
    rows_sql = []
    for edge in valid_edges:
        rows_sql.append(f'''
SELECT
  {_sql_string(edge["edge_id"])} AS edge_id,
  {_sql_string(company_id)} AS company_id,
  {_sql_string(edge["source_node_id"])} AS source_node_id,
  {_sql_string(edge["target_node_id"])} AS target_node_id,
  {_sql_string(edge["edge_type"])} AS edge_type,
  {_sql_string(edge.get("description", ""))} AS description,
  {_sql_string(edge.get("source_response_id"))} AS source_response_id,
  {float(edge.get("confidence", 0.5))} AS confidence,
  {float(edge.get("strength", edge.get("confidence", 0.5)))} AS strength,
  {int(edge.get("observed_count", 1))} AS observed_count,
  PARSE_JSON(''' + _sql_string(json.dumps(edge.get("properties", {}), ensure_ascii=False)) + f''') AS properties,
  CURRENT_TIMESTAMP() AS created_at,
  CURRENT_TIMESTAMP() AS updated_at
''')
    sql = f'''
MERGE {table} T
USING ({" UNION ALL ".join(rows_sql)}) S
ON T.edge_id = S.edge_id
WHEN MATCHED THEN UPDATE SET
  description = S.description,
  confidence = S.confidence,
  strength = S.strength,
  observed_count = T.observed_count + S.observed_count,
  properties = S.properties,
  updated_at = CURRENT_TIMESTAMP()
WHEN NOT MATCHED THEN INSERT ROW
'''.strip()
    result = execute_sql(sql)
    if invalid_count:
        result["skipped_invalid_count"] = invalid_count
    return result


def upsert_current_kpi_definition(
    company_id: str,
    record: dict,
    approved: bool = False,
    approved_by: str | None = None,
) -> dict:
    """Publish one KPI definition after explicit human approval."""
    if not approved:
        raise PermissionError("Human approval is required before updating current KPI definitions.")
    dataset = tenant_dataset_id(company_id)
    table = f"`{settings.project_id}.{dataset}.current_kpi_definitions`"
    now = "CURRENT_TIMESTAMP()"
    sql = f"""
MERGE {table} T
USING (
  SELECT
    {_sql_string(record["kpi_id"])} AS kpi_id,
    {_sql_string(company_id)} AS company_id,
    {_sql_string(record.get("common_kpi_id"))} AS common_kpi_id,
    {_sql_string(record["kpi_name"])} AS kpi_name,
    {_sql_string(record.get("kpi_domain"))} AS kpi_domain,
    {_sql_string(record.get("kpi_type"))} AS kpi_type,
    {_sql_string(record.get("description", ""))} AS description,
    {_sql_string(record.get("calculation_formula"))} AS calculation_formula,
    {_sql_string(record.get("unit"))} AS unit,
    {_sql_string(record.get("measurement_frequency"))} AS measurement_frequency,
    {_sql_string(record.get("data_source_type"))} AS data_source_type,
    {_sql_string(record.get("data_source_detail"))} AS data_source_detail,
    {_sql_string(record.get("status", "active"))} AS status,
    {_sql_string(record.get("source_kpi_candidate_id"))} AS source_kpi_candidate_id,
    {_sql_string(record.get("source_wiki_uri"))} AS source_wiki_uri,
    {_sql_string(approved_by)} AS approved_by
) S
ON T.kpi_id = S.kpi_id
WHEN MATCHED THEN UPDATE SET
  common_kpi_id = S.common_kpi_id,
  kpi_name = S.kpi_name,
  kpi_domain = S.kpi_domain,
  kpi_type = S.kpi_type,
  description = S.description,
  calculation_formula = S.calculation_formula,
  unit = S.unit,
  measurement_frequency = S.measurement_frequency,
  data_source_type = S.data_source_type,
  data_source_detail = S.data_source_detail,
  status = S.status,
  source_kpi_candidate_id = S.source_kpi_candidate_id,
  source_wiki_uri = S.source_wiki_uri,
  updated_at = {now}
WHEN NOT MATCHED THEN INSERT (
  kpi_id, company_id, common_kpi_id, kpi_name, kpi_domain, kpi_type, description,
  calculation_formula, unit, measurement_frequency, data_source_type, data_source_detail,
  status, source_kpi_candidate_id, source_wiki_uri, created_at, updated_at
) VALUES (
  S.kpi_id, S.company_id, S.common_kpi_id, S.kpi_name, S.kpi_domain, S.kpi_type,
  S.description, S.calculation_formula, S.unit, S.measurement_frequency,
  S.data_source_type, S.data_source_detail, S.status, S.source_kpi_candidate_id,
  S.source_wiki_uri, {now}, {now}
)
""".strip()
    return execute_sql(sql)


def upsert_current_focus_metric_definition(
    company_id: str,
    record: dict,
    approved: bool = False,
    approved_by: str | None = None,
) -> dict:
    """Publish one focus metric definition after explicit human approval."""
    if not approved:
        raise PermissionError(
            "Human approval is required before updating current focus metric definitions."
        )
    dataset = tenant_dataset_id(company_id)
    table = f"`{settings.project_id}.{dataset}.current_focus_metric_definitions`"
    now = "CURRENT_TIMESTAMP()"
    sql = f"""
MERGE {table} T
USING (
  SELECT
    {_sql_string(record["focus_metric_id"])} AS focus_metric_id,
    {_sql_string(company_id)} AS company_id,
    {_sql_string(record["metric_name"])} AS metric_name,
    {_sql_string(record.get("metric_category"))} AS metric_category,
    {_sql_string(record.get("description", ""))} AS description,
    {_sql_string_array(record.get("related_kpi_ids", []))} AS related_kpi_ids,
    {_sql_string_array(record.get("related_common_kpi_ids", []))} AS related_common_kpi_ids,
    {_sql_string_array(record.get("observation_signal_types", []))} AS observation_signal_types,
    {_sql_string(record.get("calculation_method"))} AS calculation_method,
    {_sql_string(record.get("unit"))} AS unit,
    {_sql_string(record.get("measurement_frequency"))} AS measurement_frequency,
    {_sql_string(record.get("trigger_condition"))} AS trigger_condition,
    {_sql_string(record.get("followup_policy"))} AS followup_policy,
    {_sql_string(record.get("status", "active"))} AS status,
    {_sql_string(record.get("source_focus_metric_candidate_id"))} AS source_focus_metric_candidate_id,
    {_sql_string(record.get("source_wiki_uri"))} AS source_wiki_uri,
    {_sql_string(approved_by)} AS approved_by
) S
ON T.focus_metric_id = S.focus_metric_id
WHEN MATCHED THEN UPDATE SET
  metric_name = S.metric_name,
  metric_category = S.metric_category,
  description = S.description,
  related_kpi_ids = S.related_kpi_ids,
  related_common_kpi_ids = S.related_common_kpi_ids,
  observation_signal_types = S.observation_signal_types,
  calculation_method = S.calculation_method,
  unit = S.unit,
  measurement_frequency = S.measurement_frequency,
  trigger_condition = S.trigger_condition,
  followup_policy = S.followup_policy,
  status = S.status,
  source_focus_metric_candidate_id = S.source_focus_metric_candidate_id,
  source_wiki_uri = S.source_wiki_uri,
  updated_at = {now}
WHEN NOT MATCHED THEN INSERT (
  focus_metric_id, company_id, metric_name, metric_category, description,
  related_kpi_ids, related_common_kpi_ids, observation_signal_types,
  calculation_method, unit, measurement_frequency, trigger_condition,
  followup_policy, status, source_focus_metric_candidate_id, source_wiki_uri,
  created_at, updated_at
) VALUES (
  S.focus_metric_id, S.company_id, S.metric_name, S.metric_category, S.description,
  S.related_kpi_ids, S.related_common_kpi_ids, S.observation_signal_types,
  S.calculation_method, S.unit, S.measurement_frequency, S.trigger_condition,
  S.followup_policy, S.status, S.source_focus_metric_candidate_id, S.source_wiki_uri,
  {now}, {now}
)
""".strip()
    return execute_sql(sql)


def propose_custom_table_ddl(company_id: str, table_id: str, purpose: str, columns: list[dict]) -> dict:
    dataset = settings.dataset_id(company_id)
    project = settings.project_id
    base_columns = ["record_id STRING NOT NULL", "company_id STRING NOT NULL"]
    custom_columns = [f'{col["name"]} {col.get("type", "STRING")}' for col in columns]
    audit_columns = ["source_response_id STRING", "properties JSON", "created_at TIMESTAMP", "updated_at TIMESTAMP", "PRIMARY KEY (record_id) NOT ENFORCED"]
    ddl = f'''
CREATE OR REPLACE TABLE `{project}.{dataset}.{table_id}` (
  {",\n  ".join(base_columns + custom_columns + audit_columns)}
);
'''.strip()
    return {"company_id": company_id, "table_id": table_id, "purpose": purpose, "ddl": ddl, "human_review_required": True}


def sample_graph_query(company_id: str, keyword: str = "") -> dict:
    dataset = settings.dataset_id(company_id)
    graph = f"`{settings.project_id}.{dataset}.{settings.bq_graph_name}`"
    where_clause = ""
    if keyword:
        where_clause = f'WHERE LOWER(n.label) LIKE LOWER("%{keyword}%")'
    gql = f'''
GRAPH {graph}
MATCH p = (n:KnowledgeNode)-[e:KnowledgeEdge]->(m:KnowledgeNode)
{where_clause}
RETURN TO_JSON(p) AS path
LIMIT 100
'''.strip()
    return {"company_id": company_id, "graph_query": gql, "note": "Notebook等では %%bigquery --graph と組み合わせて可視化する想定です。"}
