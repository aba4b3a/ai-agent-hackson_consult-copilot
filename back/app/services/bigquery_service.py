from app.core.config import settings
from app.crud.bigquery_crud import bigquery_crud
from app.schemas.bigquery import DdlResponse, ExecuteDdlResponse, GraphQueryResponse


class BigQueryService:
    def generate_core_tables_ddl(self, company_id: str) -> DdlResponse:
        dataset_id = settings.dataset_id(company_id)
        project = settings.project_id or '${PROJECT_ID}'
        graph_name = settings.bq_graph_name
        ddl = f'''
CREATE SCHEMA IF NOT EXISTS `{project}.{dataset_id}`
OPTIONS(location="{settings.location}");

CREATE OR REPLACE TABLE `{project}.{dataset_id}.survey_responses` (
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

CREATE OR REPLACE TABLE `{project}.{dataset_id}.knowledge_nodes` (
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

CREATE OR REPLACE TABLE `{project}.{dataset_id}.knowledge_edges` (
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
  PRIMARY KEY (edge_id) NOT ENFORCED
);

CREATE OR REPLACE PROPERTY GRAPH `{project}.{dataset_id}.{graph_name}`
NODE TABLES (
  `{project}.{dataset_id}.knowledge_nodes`
    KEY (node_id)
    LABEL KnowledgeNode
    PROPERTIES (company_id, node_type, label, description, confidence, status, properties)
)
EDGE TABLES (
  `{project}.{dataset_id}.knowledge_edges`
    SOURCE KEY (source_node_id) REFERENCES knowledge_nodes (node_id)
    DESTINATION KEY (target_node_id) REFERENCES knowledge_nodes (node_id)
    LABEL KnowledgeEdge
    PROPERTIES (company_id, edge_type, description, confidence, strength, observed_count, properties)
);
'''.strip()
        return DdlResponse(company_id=company_id, dataset_id=dataset_id, graph_name=graph_name, ddl=ddl)

    def create_core_tables(self, company_id: str) -> ExecuteDdlResponse:
        dataset_result = bigquery_crud.create_dataset(company_id)
        ddl = self.generate_core_tables_ddl(company_id)
        execution = bigquery_crud.execute_sql(ddl.ddl)
        execution['dataset'] = dataset_result
        return ExecuteDdlResponse(dry_run=settings.dry_run, dataset_id=ddl.dataset_id, execution=execution)

    def graph_query(self, company_id: str, keyword: str | None = None) -> GraphQueryResponse:
        dataset_id = settings.dataset_id(company_id)
        project = settings.project_id or '${PROJECT_ID}'
        graph = f'`{project}.{dataset_id}.{settings.bq_graph_name}`'
        where_clause = ''
        if keyword:
            safe = keyword.replace('"', '\\"')
            where_clause = f'WHERE LOWER(n.label) LIKE LOWER("%{safe}%") OR LOWER(m.label) LIKE LOWER("%{safe}%")'
        gql = f'''
GRAPH {graph}
MATCH p = (n:KnowledgeNode)-[e:KnowledgeEdge]->(m:KnowledgeNode)
{where_clause}
RETURN TO_JSON(p) AS path
LIMIT 100
'''.strip()
        return GraphQueryResponse(company_id=company_id, graph_query=gql, note='BigQuery Notebook 等で %%bigquery --graph と組み合わせて可視化する想定です。')


bigquery_service = BigQueryService()
