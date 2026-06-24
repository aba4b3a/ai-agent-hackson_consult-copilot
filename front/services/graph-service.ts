import { apiFetch, companyId } from "@/lib/api-client";
import type { GraphData } from "@/lib/schemas";

export const getGraphData = (): Promise<GraphData> =>
  apiFetch(`/api/v1/companies/${companyId}/graph/nodes`);
