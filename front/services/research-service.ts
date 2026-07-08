import { apiFetch, companyId } from "@/lib/api-client";

export type AssignmentStatus = "open" | "answered" | "skipped" | "expired";

export type Assignment = {
  assignment_id: string;
  company_id: string;
  followup_question_id: string;
  target_role: string;
  target_user_id: string | null;
  status: AssignmentStatus;
  created_at: string;
  expected_response_by: string | null;
  answered_at: string | null;
  followup_answer_event_id: string | null;
  question_text: string | null;
  question_category: string | null;
  reason: string | null;
  expected_answer_format: string | null;
  target_candidate_table: string | null;
  target_candidate_id: string | null;
  target_candidate_name: string | null;
};

export type AssignmentList = {
  company_id: string;
  target_role: string | null;
  items: Assignment[];
  total: number;
};

export type FollowupAnswerSubmit = {
  assignment_id: string;
  respondent_role: string;
  answer_text: string;
  answer_payload?: Record<string, unknown>;
  answered_at?: string;
};

export type FollowupAnswerResult = {
  assignment_id: string;
  followup_answer_event_id: string;
  bigquery_write_result: Record<string, unknown>;
  assignment_status: AssignmentStatus;
};

export const listAssignments = (params: {
  targetRole?: string;
  status?: AssignmentStatus;
}, targetCompanyId = companyId): Promise<AssignmentList> => {
  const search = new URLSearchParams();
  if (params.targetRole) search.set("target_role", params.targetRole);
  if (params.status) search.set("status", params.status);
  const qs = search.toString();
  return apiFetch(`/api/v1/companies/${encodeURIComponent(targetCompanyId)}/research/assignments${qs ? `?${qs}` : ""}`);
};

export const submitFollowupAnswer = (body: FollowupAnswerSubmit, targetCompanyId = companyId) =>
  apiFetch<FollowupAnswerResult>(`/api/v1/companies/${encodeURIComponent(targetCompanyId)}/research/answers`, {
    method: "POST",
    body: JSON.stringify(body),
  });
