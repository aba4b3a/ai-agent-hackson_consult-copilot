from app.core.config import settings
from app.crud.bigquery_crud import bigquery_crud
from app.schemas.survey import SurveyResponseCreate, SurveyResponseCreateResult, SurveyResponseRecord
from app.services.knowledge_service import knowledge_service
from app.utils.ids import new_id
from app.utils.time import utc_now_iso


class ResponseService:
    def create_response(self, company_id: str, data: SurveyResponseCreate) -> SurveyResponseCreateResult:
        collected_at = utc_now_iso()
        response = SurveyResponseRecord(
            response_id=new_id('resp'), company_id=company_id, collected_at=collected_at,
            qualitative_summary=data.raw_answer[:300],
            quantitative_summary=(f'numeric_value={data.numeric_value}' if data.numeric_value is not None else None),
            related_node_ids=[], related_edge_ids=[], **data.model_dump(),
        )
        nodes, edges = knowledge_service.extract_from_response(company_id, response)
        response.related_node_ids = [n.node_id for n in nodes]
        response.related_edge_ids = [e.edge_id for e in edges]
        dataset_id = settings.dataset_id(company_id)
        project = settings.project_id or '${PROJECT_ID}'
        response_persistence = bigquery_crud.insert_json_rows(f'{project}.{dataset_id}.survey_responses', [{**response.model_dump(), 'created_at': collected_at}])
        graph_persistence = knowledge_service.persist_nodes_edges(company_id, nodes, edges)
        return SurveyResponseCreateResult(response=response, extracted_nodes=[n.model_dump() for n in nodes], extracted_edges=[e.model_dump() for e in edges], persistence={'response': response_persistence, 'graph': graph_persistence})


response_service = ResponseService()
