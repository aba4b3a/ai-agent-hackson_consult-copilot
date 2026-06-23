from pydantic import BaseModel, Field


class CompanyOnboardingPrepareRequest(BaseModel):
    company_name: str = Field(..., examples=['田中美容室'])
    industry_hint: str | None = None
    size_hint: str | None = None


class CompanyOnboardingPrepareResponse(BaseModel):
    company_id: str
    company_name: str
    dataset_id: str
    core_tables_ddl: str
    initial_survey: dict
    wiki_markdown: str
    wiki_json: dict
    human_review_required: bool = True
