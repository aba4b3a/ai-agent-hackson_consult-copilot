import { apiFetch, companyId } from "@/lib/api-client";
import type { DashboardData } from "@/lib/schemas";

export const getDashboardData = (targetCompanyId = companyId): Promise<DashboardData> =>
  apiFetch(`/api/v1/companies/${encodeURIComponent(targetCompanyId)}/dashboard`);
