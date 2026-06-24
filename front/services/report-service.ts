import { apiFetch, companyId } from "@/lib/api-client";

export type SurveyQuestion = {
  question_id: string;
  question_text: string;
  answer_type: string;
  target_role: string;
  frequency: string;
};

export type SurveyFormData = {
  company_id: string;
  questions: SurveyQuestion[];
};

export const getSurveyQuestions = (): Promise<SurveyFormData> =>
  apiFetch(`/api/v1/companies/${companyId}/survey/initial`);

export const submitSurveyResponse = (body: {
  question_id: string;
  question_text: string;
  answer_type: string;
  respondent_role: string;
  raw_answer: string;
  survey_frequency: string;
}) =>
  apiFetch(`/api/v1/companies/${companyId}/survey-responses`, {
    method: "POST",
    body: JSON.stringify(body),
  });
