from app.core.config import settings
from app.crud.bigquery_crud import bigquery_crud
import json

from app.crud.storage_crud import storage_crud
from app.schemas.survey import (
    SurveyResponseCreate,
    SurveyResponseCreateResult,
    SurveyResponseRecord,
    SurveySubmissionCreate,
    SurveySubmissionResult,
)
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

    def create_submission(self, company_id: str, data: SurveySubmissionCreate) -> SurveySubmissionResult:
        collected_at = utc_now_iso()
        safe_collected_at = collected_at.replace(':', '').replace('+', 'Z')
        raw_path = f'tenants/{company_id}/raw/onboarding/initial_answers/{safe_collected_at}.json'
        raw_storage = storage_crud.upload_text(
            raw_path,
            json.dumps(data.model_dump(), ensure_ascii=False, indent=2),
            'application/json; charset=utf-8',
        )
        results = []
        for answer in data.answers:
            response_data = SurveyResponseCreate(
                question_id=answer.question_id,
                respondent_role=data.respondent_role or answer.respondent_role,
                question_text=answer.question_text,
                answer_type=answer.answer_type,
                raw_answer=answer.raw_answer,
                survey_frequency='ad_hoc',
                numeric_value=answer.numeric_value,
                answer_json={
                    **answer.answer_json,
                    'source_gcs_uri': raw_storage.get('gs_uri'),
                    'chat_transcript': data.chat_transcript,
                },
            )
            result = self.create_response(company_id, response_data)
            results.append(result.model_dump())
        return SurveySubmissionResult(
            company_id=company_id,
            answer_count=len(data.answers),
            raw_storage=raw_storage,
            response_results=results,
        )


response_service = ResponseService()
