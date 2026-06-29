import { apiFetch, companyId } from "@/lib/api-client";

export type ApprovalStatus = "pending" | "approved" | "rejected" | "applied" | "cancelled";

export type ApprovalTargetType =
  | "kpi_candidate"
  | "focus_metric_candidate"
  | "custom_table"
  | "wiki_update"
  | "schema_migration"
  | "observation_signal"
  | "other";

export type ApprovalRecord = {
  approval_id: string;
  company_id: string;
  target_type: ApprovalTargetType;
  target_id: string;
  title: string;
  summary: string;
  proposed_payload: Record<string, unknown>;
  diff_payload: Record<string, unknown> | null;
  confidence: number | null;
  reason: string | null;
  status: ApprovalStatus;
  created_by: string;
  created_at: string;
  decided_by: string | null;
  decided_at: string | null;
  decision_note: string | null;
  applied_at: string | null;
  applied_result: Record<string, unknown> | null;
};

export type ApprovalList = {
  company_id: string;
  items: ApprovalRecord[];
  total: number;
  status_filter: ApprovalStatus | null;
};

export const listApprovals = (status?: ApprovalStatus): Promise<ApprovalList> => {
  const qs = status ? `?status=${status}` : "";
  return apiFetch(`/api/v1/companies/${companyId}/approvals${qs}`);
};

export const approveApproval = (approvalId: string, decidedBy: string, note?: string) =>
  apiFetch<ApprovalRecord>(`/api/v1/companies/${companyId}/approvals/${approvalId}/approve`, {
    method: "POST",
    body: JSON.stringify({ decided_by: decidedBy, decision_note: note ?? null }),
  });

export const rejectApproval = (approvalId: string, decidedBy: string, note?: string) =>
  apiFetch<ApprovalRecord>(`/api/v1/companies/${companyId}/approvals/${approvalId}/reject`, {
    method: "POST",
    body: JSON.stringify({ decided_by: decidedBy, decision_note: note ?? null }),
  });
