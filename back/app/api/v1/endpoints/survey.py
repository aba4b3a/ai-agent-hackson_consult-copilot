from fastapi import APIRouter
from app.schemas.survey import SurveyResponseCreate, SurveyResponseCreateResult
from app.services.response_service import response_service
from app.services.survey_service import survey_service

router = APIRouter()


@router.get('/{company_id}/survey/initial')
def get_initial_survey(company_id: str):
    return survey_service.generate_common_initial_survey(company_id)


@router.post('/{company_id}/survey-responses', response_model=SurveyResponseCreateResult)
def create_survey_response(company_id: str, data: SurveyResponseCreate):
    return response_service.create_response(company_id, data)
