import type { DashboardData } from "@/lib/schemas";

const mockDashboardData: DashboardData = {
  consultant: {
    name: "Consultant",
    subtitle: "8 client portfolios",
    isLive: true,
  },
  hero: {
    title: "今週の重要発見",
    count: 12,
    summary: "幸福度 +38% / 離合品率 +21%",
  },
  insights: [
    {
      id: "insight-1",
      title: "A社: 価格不満が急増",
      description: "小規模小売セグメントで顕著",
      meta: "Fact: 21 mentions / Hypothesis: 競合値下げ影響",
      priority: "danger",
    },
    {
      id: "insight-2",
      title: "B社: リピート要因が明確化",
      description: "サポート品質と柔軟性が評価",
      meta: "Evidence: 18 quotes / KPI linked",
      priority: "success",
    },
  ],
  portfolio: [
    { id: "client-a", name: "A社", status: "3 alerts" },
    { id: "client-b", name: "B社", status: "learning" },
    { id: "client-c", name: "C社", status: "quiet" },
  ],
  nextActions: [
    {
      id: "action-1",
      title: "追加調査を送信",
      description: "価格比較の仮説を市場調査へ確認",
    },
    {
      id: "action-2",
      title: "週次レポート作成",
      description: "根拠付き Discovery Reportを生成",
    },
  ],
};

export const getDashboardData = async (): Promise<DashboardData> => {
  // Static Export 対応: app/api は使わず、実API化する場合もクライアントから外部APIを呼びます。
  await new Promise((resolve) => setTimeout(resolve, 120));
  return mockDashboardData;
};
