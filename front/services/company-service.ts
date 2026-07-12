import { apiFetch } from "@/lib/api-client";

export type CompanyOnboardingPrepareRequest = {
  company_name: string;
  industry_hint?: string | null;
  size_hint?: string | null;
};

export type CompanyOnboardingPrepareResponse = {
  company_id: string;
  company_name: string;
  dataset_id: string;
  core_tables_ddl: string;
  initial_survey: Record<string, unknown>;
  wiki_markdown: string;
  wiki_json: Record<string, unknown>;
  human_review_required: boolean;
};

export type ExecuteDdlResponse = {
  dry_run: boolean;
  dataset_id: string;
  execution: Record<string, unknown>;
};

export const prepareCompanyOnboarding = (
  targetCompanyId: string,
  body: CompanyOnboardingPrepareRequest,
): Promise<CompanyOnboardingPrepareResponse> =>
  apiFetch(`/api/v1/companies/${encodeURIComponent(targetCompanyId)}/onboarding/prepare`, {
    method: "POST",
    body: JSON.stringify(body),
  });

export const createCompanyCoreTables = (targetCompanyId: string): Promise<ExecuteDdlResponse> =>
  apiFetch(`/api/v1/companies/${encodeURIComponent(targetCompanyId)}/bigquery/core-tables`, {
    method: "POST",
  });

export type CompanyRecord = {
  company_id: string;
  company_name: string;
  company_size_segment: string | null;
  onboarding_status: string | null;
  active_status: string | null;
  created_at: string;
  updated_at: string | null;
};

export type CompanyCreateRequest = {
  company_id: string;
  company_name: string;
  industry_hint?: string | null;
  size_hint?: string | null;
};

export const listCompanies = (): Promise<CompanyRecord[]> => apiFetch(`/api/v1/companies`);

export const createCompanyMaster = (body: CompanyCreateRequest): Promise<CompanyRecord> =>
  apiFetch(`/api/v1/companies`, {
    method: "POST",
    body: JSON.stringify(body),
  });

export const deleteCompanyMaster = (targetCompanyId: string): Promise<CompanyRecord> =>
  apiFetch(`/api/v1/companies/${encodeURIComponent(targetCompanyId)}`, {
    method: "DELETE",
  });
