from fastapi import APIRouter, HTTPException
from app.schemas.company import (
    CompanyCreate,
    CompanyOnboardingPrepareRequest,
    CompanyOnboardingPrepareResponse,
    CompanyRecord,
)
from app.services.company_service import company_service
from app.services.onboarding_service import onboarding_service

router = APIRouter()


@router.post('/{company_id}/onboarding/prepare', response_model=CompanyOnboardingPrepareResponse)
def prepare_onboarding(company_id: str, data: CompanyOnboardingPrepareRequest):
    return onboarding_service.prepare(company_id, data)


@router.post('', response_model=CompanyRecord)
def create_company(data: CompanyCreate):
    try:
        return company_service.create(
            data.company_id, data.company_name, data.industry_hint, data.size_hint
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.delete('/{company_id}', response_model=CompanyRecord)
def delete_company(company_id: str):
    """Logical delete only — flips active_status to inactive. The company's
    BigQuery data (core + tenant datasets) is left untouched."""
    try:
        return company_service.deactivate(company_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"company {company_id} not found")
