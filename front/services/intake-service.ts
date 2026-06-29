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

export const getInitialSurvey = (): Promise<SurveyTemplate> =>
  apiFetch(`/api/v1/companies/${companyId}/survey/initial`);

export const submitInitialSurvey = (body: {
  respondent_role: string;
  answers: SurveyAnswerPayload[];
  chat_transcript: { role: "assistant" | "user"; text: string }[];
}) =>
  apiFetch(`/api/v1/companies/${companyId}/survey/initial/submissions`, {
    method: "POST",
    body: JSON.stringify(body),
  });
