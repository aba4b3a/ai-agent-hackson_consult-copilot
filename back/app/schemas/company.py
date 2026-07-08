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


class CompanyCreate(BaseModel):
    company_id: str
    company_name: str
    industry_hint: str | None = None
    size_hint: str | None = None


class CompanyRecord(BaseModel):
    company_id: str
    company_name: str
    legal_name: str | None = None
    industry_code: str | None = None
    industry_name: str | None = None
    sub_industry_code: str | None = None
    sub_industry_name: str | None = None
    business_type: str | None = None
    company_size_segment: str | None = None
    employee_count: int | None = None
    annual_revenue_range: str | None = None
    region_country: str | None = None
    region_prefecture: str | None = None
    region_city: str | None = None
    primary_sales_channels: list[str] = Field(default_factory=list)
    primary_customer_types: list[str] = Field(default_factory=list)
    primary_revenue_models: list[str] = Field(default_factory=list)
    onboarding_status: str | None = None
    active_status: str | None = None
    created_at: str
    updated_at: str | None = None
