import { apiFetch, companyId } from "@/lib/api-client";
import type { KnowledgeData } from "@/lib/schemas";

export const getKnowledgeData = (): Promise<KnowledgeData> =>
  apiFetch(`/api/v1/companies/${companyId}/knowledge/stats`);
