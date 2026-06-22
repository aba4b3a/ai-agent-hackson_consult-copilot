import type { KnowledgeData } from "@/lib/schemas";

const mockKnowledgeData: KnowledgeData = {
  header: {
    title: "Knowledge Formation",
    subtitle: "ナレッジの形成・集約状況を可視化",
    statusLabel: "Knowledge Asset",
    statusDescription: "Formation status",
  },
  health: {
    score: 78,
    title: "Knowledge Health",
    signals: ["Evidence linked", "Relations growing", "Hypotheses active"],
  },
  accumulation: [
    { id: "acc-1", label: "Q&A", value: 428, tone: "blue" },
    { id: "acc-2", label: "Entity", value: 92, tone: "green" },
    { id: "acc-3", label: "Rule", value: 217, tone: "yellow" },
    { id: "acc-4", label: "H&P", value: 24, tone: "purple" },
  ],
  pipeline: [
    { id: "pipe-1", label: "Raw notes indexed", value: 72, tone: "blue" },
    { id: "pipe-2", label: "Structured knowledge", value: 51, tone: "teal" },
    { id: "pipe-3", label: "Active hypotheses", value: 8, tone: "amber" },
  ],
  gap: {
    title: "Knowledge Gaps",
    description: "価格不満は多いが、失注理由の把握が不足",
    tags: [
      { id: "gap-1", label: "needs intel", tone: "rose" },
      { id: "gap-2", label: "ask field", tone: "blue" },
    ],
  },
  recentKnowledge: [
    "競合A — 価格比較 — 小規模小売",
    "サポート品質 — 継続率 — B社",
    "解約不安 — 製品B — 問い合わせ後",
  ],
};

export const getKnowledgeData = async (): Promise<KnowledgeData> => {
  // Static Export 対応: app/api は使わず、実API化する場合もクライアントから外部APIを呼びます。
  await new Promise((resolve) => setTimeout(resolve, 120));
  return mockKnowledgeData;
};
