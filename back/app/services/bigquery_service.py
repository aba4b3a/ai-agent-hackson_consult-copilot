from google.api_core.exceptions import GoogleAPIError

from app.core.config import settings
from app.crud.bigquery_crud import bigquery_crud
from app.schemas.bigquery import DdlResponse, ExecuteDdlResponse, GraphQueryResponse


class BigQueryService:
    def generate_core_tables_ddl(self, company_id: str) -> DdlResponse:
        dataset_id = settings.dataset_id()
        project = settings.project_id or '${PROJECT_ID}'
        graph_name = f'{settings.safe_company_id(company_id)}_{settings.bq_graph_name}'
        survey_responses = settings.company_table(company_id, 'survey_responses')
        knowledge_nodes = settings.company_table(company_id, 'knowledge_nodes')
        knowledge_edges = settings.company_table(company_id, 'knowledge_edges')
        ddl = f'''
CREATE SCHEMA IF NOT EXISTS `{project}.{dataset_id}`
OPTIONS(location="{settings.location}");

CREATE TABLE IF NOT EXISTS `{project}.{dataset_id}.{survey_responses}` (
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

CREATE TABLE IF NOT EXISTS `{project}.{dataset_id}.{knowledge_nodes}` (
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

CREATE TABLE IF NOT EXISTS `{project}.{dataset_id}.{knowledge_edges}` (
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
  `{project}.{dataset_id}.{knowledge_nodes}` AS knowledge_nodes
    KEY (node_id)
    LABEL KnowledgeNode
    PROPERTIES (company_id, node_type, label, description, confidence, status, properties)
)
EDGE TABLES (
  `{project}.{dataset_id}.{knowledge_edges}` AS knowledge_edges
    SOURCE KEY (source_node_id) REFERENCES knowledge_nodes (node_id)
    DESTINATION KEY (target_node_id) REFERENCES knowledge_nodes (node_id)
    LABEL KnowledgeEdge
    PROPERTIES (company_id, edge_type, description, confidence, strength, observed_count, properties)
);
'''.strip()
        return DdlResponse(company_id=company_id, dataset_id=dataset_id, graph_name=graph_name, ddl=ddl)

    def create_core_tables(self, company_id: str) -> ExecuteDdlResponse:
        dataset_result = bigquery_crud.create_dataset()
        ddl = self.generate_core_tables_ddl(company_id)
        execution = bigquery_crud.execute_sql(ddl.ddl)
        execution['dataset'] = dataset_result
        return ExecuteDdlResponse(dry_run=settings.dry_run, dataset_id=ddl.dataset_id, execution=execution)

    def graph_query(
        self,
        company_id: str,
        keyword: str | None = None,
        node_type: str | None = None,
        target_type: str | None = None,
        edge_type: str | None = None,
        hops: int = 1,
    ) -> GraphQueryResponse:
        """Design doc §10.3's use cases are type-directed (e.g. "start from a
        Signal, follow LEADING_INDICATOR_OF to KPI"), not a generic "any two
        connected nodes" traversal — node_type/edge_type are plain
        properties on the single KnowledgeNode/KnowledgeEdge GQL labels
        (see the CREATE PROPERTY GRAPH DDL), not distinct graph labels, so
        expressing those use cases means filtering on them in WHERE, not in
        MATCH. hops supports the multi-hop cases (e.g. TacitKnowledge ->
        PROTECTS -> KPI -> DRIVES -> CustomerSegment) via GQL's quantified
        edge pattern.
        """
        dataset_id = settings.dataset_id()
        project = settings.project_id or '${PROJECT_ID}'
        graph_name = f'{settings.safe_company_id(company_id)}_{settings.bq_graph_name}'
        graph = f'`{project}.{dataset_id}.{graph_name}`'
        safe_hops = min(max(hops, 1), 3)

        def _escape(value: str) -> str:
            return value.replace('"', '\\"')

        clauses = []
        if node_type:
            clauses.append(f'n.node_type = "{_escape(node_type)}"')
        if target_type:
            clauses.append(f'm.node_type = "{_escape(target_type)}"')
        if edge_type:
            clauses.append(f'e.edge_type = "{_escape(edge_type)}"')
        if keyword:
            safe = _escape(keyword)
            clauses.append(f'(LOWER(n.label) LIKE LOWER("%{safe}%") OR LOWER(m.label) LIKE LOWER("%{safe}%"))')
        where_clause = f'WHERE {" AND ".join(clauses)}' if clauses else ''
        edge_pattern = '-[e:KnowledgeEdge]->' if safe_hops == 1 else f'-[e:KnowledgeEdge]->{{1,{safe_hops}}}'
        gql = f'''
GRAPH {graph}
MATCH p = (n:KnowledgeNode){edge_pattern}(m:KnowledgeNode)
{where_clause}
RETURN TO_JSON(p) AS path
LIMIT 100
'''.strip()
        if settings.dry_run:
            return GraphQueryResponse(
                company_id=company_id, graph_query=gql, executed=False, results=[],
                note='dry_run: query not executed.',
            )
        try:
            rows = bigquery_crud.query_rows(gql)
        except GoogleAPIError as exc:
            return GraphQueryResponse(
                company_id=company_id, graph_query=gql, executed=False, results=[],
                note=f'GQL query failed (property graph may not exist yet for this company): {exc}',
            )
        results = [row.get('path') for row in rows]
        return GraphQueryResponse(
            company_id=company_id, graph_query=gql, executed=True, results=results,
            note=f'{len(results)} path(s) returned directly from the BigQuery property graph.',
        )


bigquery_service = BigQueryService()
