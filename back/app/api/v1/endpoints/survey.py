from fastapi import APIRouter
from app.schemas.survey import (
    InitialSurveyStatus,
    SurveyResponseCreate,
    SurveyResponseCreateResult,
    SurveySubmissionCreate,
    SurveySubmissionResult,
)
from app.services.response_service import response_service
from app.services.survey_service import survey_service

router = APIRouter()


@router.get('/{company_id}/survey/initial')
def get_initial_survey(company_id: str):
    return survey_service.generate_common_initial_survey(company_id)


@router.get('/{company_id}/survey/initial/submissions', response_model=InitialSurveyStatus)
def get_initial_survey_status(company_id: str):
    return survey_service.get_initial_survey_status(company_id)


@router.post('/{company_id}/survey-responses', response_model=SurveyResponseCreateResult)
def create_survey_response(company_id: str, data: SurveyResponseCreate):
    return response_service.create_response(company_id, data)


@router.post('/{company_id}/survey/initial/submissions', response_model=SurveySubmissionResult)
def create_initial_survey_submission(company_id: str, data: SurveySubmissionCreate):
    return response_service.create_submission(company_id, data)
