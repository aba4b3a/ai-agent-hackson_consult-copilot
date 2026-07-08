import { apiFetch, companyId } from "@/lib/api-client";
import type { ReportCopilotData } from "@/lib/schemas";

export const getReportCopilotData = (targetCompanyId = companyId): Promise<ReportCopilotData> =>
  apiFetch(`/api/v1/companies/${encodeURIComponent(targetCompanyId)}/report/monthly`);

export const sendCopilotMessage = (message: string, sessionId?: string, targetCompanyId = companyId) =>
  apiFetch<{ reply: string; session_id: string }>(
    `/api/v1/companies/${encodeURIComponent(targetCompanyId)}/report/copilot`,
    {
      method: "POST",
      body: JSON.stringify({ message, session_id: sessionId }),
    }
  );
