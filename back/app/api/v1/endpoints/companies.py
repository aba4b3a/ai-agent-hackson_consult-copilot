from fastapi import APIRouter
from app.schemas.company import CompanyOnboardingPrepareRequest, CompanyOnboardingPrepareResponse
from app.services.onboarding_service import onboarding_service

router = APIRouter()


@router.post('/{company_id}/onboarding/prepare', response_model=CompanyOnboardingPrepareResponse)
def prepare_onboarding(company_id: str, data: CompanyOnboardingPrepareRequest):
    return onboarding_service.prepare(company_id, data)
