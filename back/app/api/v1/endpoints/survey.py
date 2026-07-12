from fastapi import APIRouter, BackgroundTasks
from app.schemas.survey import (
    InitialSurveyStatus,
    IntakeAssistRequest,
    IntakeAssistResponse,
    SurveyResponseCreate,
    SurveyResponseCreateResult,
    SurveySubmissionCreate,
    SurveySubmissionResult,
)
from app.services.intake_assist_service import intake_assist_service
from app.services.onboarding_service import onboarding_service
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
def create_initial_survey_submission(
    company_id: str, data: SurveySubmissionCreate, background_tasks: BackgroundTasks
):
    result = response_service.create_submission(company_id, data)
    # create_submission processes answers in order, so response_results aligns
    # 1:1 with data.answers. The agent uses these ids as source_response_id on
    # extracted knowledge-graph nodes/edges (evidence-layer reference).
    for answer, response_result in zip(data.answers, result.response_results):
        answer.response_id = response_result['response']['response_id']
    background_tasks.add_task(onboarding_service.run_agent_onboarding, company_id, data.answers)
    return result


@router.post('/{company_id}/survey/initial/assist', response_model=IntakeAssistResponse)
async def intake_assist(company_id: str, data: IntakeAssistRequest):
    """「AIに補足する」チャットの1往復。提出前のためBQには書き込まない —
    会話は提出時に chat_messages / chat_transcript として保存される。"""
    return await intake_assist_service.assist(company_id, data)


@router.post('/{company_id}/survey/initial/onboarding/retry')
def retry_initial_survey_onboarding(company_id: str, background_tasks: BackgroundTasks):
    """Manually retry after onboarding_status='failed' (e.g. a transient
    agent-connectivity error) — re-runs whichever stage actually failed
    without requiring the user to resubmit any answers."""
    background_tasks.add_task(onboarding_service.retry_failed_onboarding, company_id)
    return {'status': 'retry_scheduled'}
