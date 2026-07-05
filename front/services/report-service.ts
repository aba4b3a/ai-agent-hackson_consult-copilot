import { apiFetch, companyId } from "@/lib/api-client";
import type { ReportData } from "@/lib/schemas";

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

export const getSurveyQuestions = (targetCompanyId = companyId): Promise<SurveyFormData> =>
  apiFetch(`/api/v1/companies/${encodeURIComponent(targetCompanyId)}/survey/initial`);

export const submitSurveyResponse = (body: {
  question_id: string;
  question_text: string;
  answer_type: string;
  respondent_role: string;
  raw_answer: string;
  survey_frequency: string;
}, targetCompanyId = companyId) =>
  apiFetch(`/api/v1/companies/${encodeURIComponent(targetCompanyId)}/survey-responses`, {
    method: "POST",
    body: JSON.stringify(body),
  });

export const getReportData = async (targetCompanyId = companyId): Promise<ReportData> => {
  try {
    return await apiFetch(`/api/v1/companies/${encodeURIComponent(targetCompanyId)}/report-chat`);
  } catch {
    return {
      header: {
        statusLabel: "INTAKE",
        statusDescription: "追加質問チャット",
        title: "現場の補足を集める",
        subtitle: "定型フォームで足りない文脈を短い会話で補足します",
      },
      topic: "価格・競合・顧客変化など、KPI候補に関係する論点を確認します",
      messages: [
        {
          id: "m1",
          role: "assistant",
          body: "今週、顧客から価格や競合について聞かれたことはありましたか？",
        },
        {
          id: "m2",
          role: "user",
          body: "学生のお客様から、唐揚げ定食が高いという声が3件ありました。",
        },
      ],
      extraction: {
        title: "抽出候補",
        observation: "学生顧客から価格関連発言が週3件発生",
        entities: "顧客層: 学生 / 商品: 唐揚げ定食 / シグナル: price_complaint",
      },
      voiceAction: {
        title: "音声で補足",
        description: "短い会話として回答を追加できます",
      },
      urlPlaceholder: "追加メモや参照URL",
    };
  }
};
