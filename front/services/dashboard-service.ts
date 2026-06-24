import { apiFetch, companyId } from "@/lib/api-client";
import type { DashboardData } from "@/lib/schemas";

export const getDashboardData = (): Promise<DashboardData> =>
  apiFetch(`/api/v1/companies/${companyId}/dashboard`);
