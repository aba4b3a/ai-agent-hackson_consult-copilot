import { apiFetch, companyId } from "@/lib/api-client";
import type { KnowledgeData } from "@/lib/schemas";

export const getKnowledgeData = (targetCompanyId = companyId): Promise<KnowledgeData> =>
  apiFetch(`/api/v1/companies/${encodeURIComponent(targetCompanyId)}/knowledge/stats`);
