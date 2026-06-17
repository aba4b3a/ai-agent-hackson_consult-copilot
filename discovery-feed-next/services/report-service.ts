import type { ReportData } from "@/lib/schemas";

const mockReportData: ReportData = {
  header: {
    statusLabel: "Business Intake",
    statusDescription: "Voice conversation form",
    title: "Report Chat",
    subtitle: "音声記録・発話で対話的に深掘り",
  },
  topic: "本日の重点観察: 価格比較 / 失注理由",
  messages: [
    {
      id: "msg-1",
      role: "assistant",
      body: "今日は問い合わせが多かったですか？必要なら声で答えてください",
      aside: "-",
    },
    {
      id: "msg-2",
      role: "user",
      body: "はい、商品Aの価格について他社比較の質問が多かったです。",
    },
    {
      id: "msg-3",
      role: "assistant",
      body: "どの顧客層で多かったですか？小規模小売／既存顧客／新規",
      aside: " ",
    },
    {
      id: "msg-4",
      role: "user",
      body: "小規模小売の新規検討が多かったです。",
    },
  ],
  extraction: {
    title: "AI extraction preview",
    observation: "価格比較の問い合わせ増加",
    entities: "商品A / 小規模小売 / 競合",
  },
  voiceAction: {
    title: "Hold to talk",
    description: "AIが聞き返し、発話で回答",
  },
  urlPlaceholder: "URLフォームからも貼付可能",
};

export const getReportData = async (): Promise<ReportData> => {
  // Static Export 対応: app/api は使わず、実API化する場合もクライアントから外部APIを呼びます。
  await new Promise((resolve) => setTimeout(resolve, 120));
  return mockReportData;
};
