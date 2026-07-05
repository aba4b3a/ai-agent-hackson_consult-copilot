import { apiFetch, companyId } from "@/lib/api-client";
import type { KnowledgeData, KpiTrendsData } from "@/lib/schemas";

export const getKnowledgeData = (targetCompanyId = companyId): Promise<KnowledgeData> =>
  apiFetch(`/api/v1/companies/${encodeURIComponent(targetCompanyId)}/knowledge/stats`);

export const getKpiTrends = (targetCompanyId = companyId): Promise<KpiTrendsData> =>
  apiFetch(`/api/v1/companies/${encodeURIComponent(targetCompanyId)}/knowledge/kpi-trends`);
