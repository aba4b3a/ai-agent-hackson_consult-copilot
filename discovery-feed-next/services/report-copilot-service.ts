import type { ReportCopilotData } from "@/lib/schemas";

const mockReportCopilotData: ReportCopilotData = {
  header: {
    title: "Report Copilot",
    subtitle: "事実と仮説を分けてコンサルに提示",
  },
  weekly: {
    title: "Weekly Discovery",
    period: "A社 / 2026-W24",
    summary: "3 facts / 2 hypotheses / 4 evidence groups",
  },
  highlights: [
    {
      id: "fact-1",
      kind: "FACT",
      tone: "green",
      title: "価格関連発言が増加",
      description: "31件 / 14顧客 / 前週比 +38%",
      meta: "顧客不満 → 競合比較",
    },
    {
      id: "hypothesis-1",
      kind: "HYPOTHESIS",
      tone: "yellow",
      title: "競合A値下げの影響か",
      description: "競合A言及が価格不満と同時増加",
      meta: "追加確認を推奨",
    },
  ],
  snippets: [
    "他社の方が安いと聞いた",
    "見積比較したい",
    "A社キャンペーンを見た",
  ],
  recommendation: {
    title: "Recommended observation",
    description: "次週は失注理由と見積比較有無を確認",
    actionLabel: "send intake",
  },
  ctaLabel: "Generate report",
};

export const getReportCopilotData = async (): Promise<ReportCopilotData> => {
  // Static Export 対応: app/api は使わず、実API化する場合もクライアントから外部APIを呼びます。
  await new Promise((resolve) => setTimeout(resolve, 120));
  return mockReportCopilotData;
};
