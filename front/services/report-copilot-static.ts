import { apiFetch, companyId } from "@/lib/api-client";
import type { ReportCopilotData } from "@/lib/schemas";

export const getReportCopilotData = (): Promise<ReportCopilotData> =>
  apiFetch(`/api/v1/companies/${companyId}/report/weekly`);
