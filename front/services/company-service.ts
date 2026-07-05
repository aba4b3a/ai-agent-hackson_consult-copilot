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
