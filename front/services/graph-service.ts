import { apiFetch, companyId } from "@/lib/api-client";
import type { GraphData } from "@/lib/schemas";

export const getGraphData = (targetCompanyId = companyId): Promise<GraphData> =>
  apiFetch(`/api/v1/companies/${encodeURIComponent(targetCompanyId)}/graph/nodes`);
