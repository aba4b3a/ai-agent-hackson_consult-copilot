import { apiFetch, companyId } from "@/lib/api-client";
import type { ReportCopilotData } from "@/lib/schemas";

export const getReportCopilotData = (): Promise<ReportCopilotData> =>
  apiFetch(`/api/v1/companies/${companyId}/report/weekly`);

export const sendCopilotMessage = (message: string, sessionId?: string) =>
  apiFetch<{ reply: string; session_id: string }>(
    `/api/v1/companies/${companyId}/report/copilot`,
    {
      method: "POST",
      body: JSON.stringify({ message, session_id: sessionId }),
    }
  );
