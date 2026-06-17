import type { GraphData } from "@/lib/schemas";

const mockGraphData: GraphData = {
  header: {
    title: "Knowledge Graph",
    subtitle: "関係を見える／グラフを切り替える",
  },
  filters: ["顧客・課題", "競合影響", "KPI因果", "仮説"],
  map: {
    title: "Segment Issue Map",
    nodes: [
      { id: "n-1", label: "価格", tone: "rose", position: "topLeft" },
      { id: "n-2", label: "競合", tone: "cyan", position: "topRight" },
      { id: "n-3", label: "継続率", tone: "amber", position: "bottomLeft" },
      { id: "n-4", label: "導入率", tone: "violet", position: "bottomRight" },
      { id: "n-5", label: "小規模\n小売", tone: "blue", position: "center" },
    ],
    stats: "Nodes 92 / Relations 217 / Evidence Linked 78%",
  },
  views: [
    { id: "view-1", label: "Issue", tone: "blue" },
    { id: "view-2", label: "KPI", tone: "green" },
    { id: "view-3", label: "Comp", tone: "yellow" },
    { id: "view-4", label: "Hyp", tone: "purple" },
  ],
  relation: {
    title: "Selected relation",
    segment: "小規模小売 — 価格不満",
    evidence: "Evidence: 31 quotes / 14 customers",
    customers: "Customers: 競合A傘下げの影響",
    hypothesis: "Hypothesis: 競合A値下げの影響",
    confidence: 72,
  },
  lens: [
    { id: "lens-1", label: "Fact graph", value: "観測された関係" },
    { id: "lens-2", label: "Hypothesis graph", value: "可能性の関係" },
    { id: "lens-3", label: "Gap graph", value: "足りない証拠" },
    { id: "lens-4", label: "KPI graph", value: "指標との関連" },
  ],
};

export const getGraphData = async (): Promise<GraphData> => {
  // Static Export 対応: app/api は使わず、実API化する場合もクライアントから外部APIを呼びます。
  await new Promise((resolve) => setTimeout(resolve, 120));
  return mockGraphData;
};
