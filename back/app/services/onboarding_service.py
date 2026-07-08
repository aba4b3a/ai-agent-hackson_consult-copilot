from app.core.config import settings
from app.schemas.company import CompanyOnboardingPrepareRequest, CompanyOnboardingPrepareResponse
from app.services.bigquery_service import bigquery_service
from app.services.survey_service import survey_service
from app.services.wiki_service import wiki_service


class OnboardingService:
    def prepare(self, company_id: str, data: CompanyOnboardingPrepareRequest) -> CompanyOnboardingPrepareResponse:
        initial_survey = survey_service.generate_common_initial_survey(company_id)
        ddl = bigquery_service.generate_core_tables_ddl(company_id)
        wiki_markdown, wiki_json = wiki_service.render_initial_wiki(company_id, data.company_name, initial_survey)
        if data.industry_hint:
            wiki_json['industry_hint'] = data.industry_hint
        if data.size_hint:
            wiki_json['size_hint'] = data.size_hint
        return CompanyOnboardingPrepareResponse(company_id=company_id, company_name=data.company_name, dataset_id=settings.dataset_id(), core_tables_ddl=ddl.ddl, initial_survey=initial_survey, wiki_markdown=wiki_markdown, wiki_json=wiki_json)


onboarding_service = OnboardingService()
