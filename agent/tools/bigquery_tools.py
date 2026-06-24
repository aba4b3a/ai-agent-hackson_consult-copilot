from __future__ import annotations

import json
import os
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
    return "'" + value.replace("'", "\\'") + "'"


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


def upsert_knowledge_nodes(company_id: str, nodes: list[dict]) -> dict:
    if not nodes:
        return {"skipped": True, "reason": "no nodes"}
    dataset = settings.dataset_id(company_id)
    table = f"`{settings.project_id}.{dataset}.knowledge_nodes`"
    rows_sql = []
    for node in nodes:
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
    return execute_sql(sql)


def upsert_knowledge_edges(company_id: str, edges: list[dict]) -> dict:
    if not edges:
        return {"skipped": True, "reason": "no edges"}
    dataset = settings.dataset_id(company_id)
    table = f"`{settings.project_id}.{dataset}.knowledge_edges`"
    rows_sql = []
    for edge in edges:
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
