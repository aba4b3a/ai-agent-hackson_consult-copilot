import { apiFetch, companyId } from "@/lib/api-client";

export type SurveyChoice = {
  value: string;
  label: string;
  description?: string | null;
};

export type SurveyValidation = {
  required: boolean;
  min_value?: number | null;
  max_value?: number | null;
  min_length?: number | null;
  max_length?: number | null;
  unit?: string | null;
  step?: number | null;
};

export type SurveyQuestion = {
  question_id: string;
  company_id: string;
  version: string;
  question_order: number;
  question_text: string;
  short_label: string;
  help_text?: string | null;
  target_role: string;
  answer_type: "single_choice" | "multiple_choice" | "numeric" | "text" | "long_text" | "rating" | "date" | "json";
  frequency: string;
  question_category: string;
  purpose: string;
  placeholder?: string | null;
  choices: SurveyChoice[];
  validation: SurveyValidation;
};

export type SurveyTemplate = {
  template_id: string;
  company_id: string;
  survey_type: string;
  version: string;
  title: string;
  description: string;
  storage_path: string;
  questions: SurveyQuestion[];
};

export type SurveyAnswerPayload = {
  question_id: string;
  question_text: string;
  answer_type: SurveyQuestion["answer_type"];
  respondent_role: string;
  raw_answer: string;
  numeric_value?: number | null;
  answer_json?: Record<string, unknown>;
};

export type SurveyAnswerRead = {
  question_id: string;
  question_text: string;
  answer_type: SurveyQuestion["answer_type"];
  respondent_role: string;
  raw_answer: string;
  numeric_value?: number | null;
  answer_json?: Record<string, unknown>;
  collected_at: string;
};

export type OnboardingStatus =
  | "pending"
  | "processing"
  | "awaiting_followup"
  | "finalizing"
  | "completed"
  | "failed"
  | null;

export type InitialSurveyStatus = {
  company_id: string;
  answered: boolean;
  answered_count: number;
  total_count: number;
  answers: SurveyAnswerRead[];
  onboarding_status?: OnboardingStatus;
  onboarding_error?: string | null;
};

export const getInitialSurvey = (targetCompanyId = companyId): Promise<SurveyTemplate> =>
  apiFetch(`/api/v1/companies/${encodeURIComponent(targetCompanyId)}/survey/initial`);

export const getInitialSurveyStatus = (targetCompanyId = companyId): Promise<InitialSurveyStatus> =>
  apiFetch(`/api/v1/companies/${encodeURIComponent(targetCompanyId)}/survey/initial/submissions`);

export const retryOnboarding = (targetCompanyId = companyId) =>
  apiFetch(`/api/v1/companies/${encodeURIComponent(targetCompanyId)}/survey/initial/onboarding/retry`, {
    method: "POST",
  });

export const submitInitialSurvey = (body: {
  respondent_role: string;
  answers: SurveyAnswerPayload[];
  chat_transcript: { role: "assistant" | "user"; text: string }[];
}, targetCompanyId = companyId) =>
  apiFetch(`/api/v1/companies/${encodeURIComponent(targetCompanyId)}/survey/initial/submissions`, {
    method: "POST",
    body: JSON.stringify(body),
  });

export type IntakeAssistChatMessage = { role: "assistant" | "user"; text: string };

export const sendIntakeAssistMessage = (
  body: {
    question_id: string;
    question_text: string;
    purpose?: string | null;
    current_answer: string;
    chat_history: IntakeAssistChatMessage[];
    user_message: string;
  },
  targetCompanyId = companyId,
): Promise<{
  company_id: string;
  question_id: string;
  reply: string;
  mode: "followup" | "summary";
  answer_draft?: string | null;
}> =>
  apiFetch(`/api/v1/companies/${encodeURIComponent(targetCompanyId)}/survey/initial/assist`, {
    method: "POST",
    body: JSON.stringify(body),
  });
