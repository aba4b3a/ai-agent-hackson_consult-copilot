export type Priority = "danger" | "success" | "neutral";

export type DiscoveryInsight = {
  id: string;
  title: string;
  description: string;
  meta: string;
  priority: Priority;
};

export type PortfolioClient = {
  id: string;
  name: string;
  status: string;
};

export type NextAction = {
  id: string;
  title: string;
  description: string;
};

export type DashboardData = {
  consultant: {
    name: string;
    subtitle: string;
    isLive: boolean;
  };
  hero: {
    title: string;
    count: number;
    summary: string;
  };
  insights: DiscoveryInsight[];
  portfolio: PortfolioClient[];
  nextActions: NextAction[];
};

export type KnowledgeMetric = {
  id: string;
  label: string;
  value: number;
  tone: "blue" | "green" | "yellow" | "purple";
};

export type PipelineItem = {
  id: string;
  label: string;
  value: number;
  tone: "blue" | "teal" | "amber";
};

export type GapTag = {
  id: string;
  label: string;
  tone: "rose" | "blue";
};

export type KnowledgeData = {
  header: {
    title: string;
    subtitle: string;
    statusLabel: string;
    statusDescription: string;
  };
  health: {
    score: number;
    title: string;
    signals: string[];
  };
  accumulation: KnowledgeMetric[];
  pipeline: PipelineItem[];
  gap: {
    title: string;
    description: string;
    tags: GapTag[];
  };
  recentKnowledge: string[];
};


export type SegmentNode = {
  id: string;
  label: string;
  tone: "rose" | "cyan" | "amber" | "violet" | "blue";
  position: "topLeft" | "topRight" | "bottomLeft" | "bottomRight" | "center";
  nodeType?: string;
  description?: string;
  x?: number;
  y?: number;
  size?: "sm" | "md" | "lg";
  meta?: string;
  value?: number | null;
  unit?: string | null;
};

export type GraphEdge = {
  id: string;
  source: string;
  target: string;
  label: string;
  tone: "blue" | "rose" | "amber" | "violet" | "slate";
  strength: number;
  description?: string;
};

export type GraphView = {
  id: string;
  label: string;
  tone: "blue" | "green" | "yellow" | "purple";
};

export type KnowledgeLensItem = {
  id: string;
  label: string;
  value: string;
};

export type KpiTrendPoint = {
  collected_at: string | null;
  value: number | null;
};

export type KpiTrend = {
  id: string;
  label: string;
  category: string;
  description: string;
  latest_value: number | null;
  latest_collected_at: string | null;
  direction: "up" | "down" | "flat" | "new" | "no_data";
  history: KpiTrendPoint[];
  related_kpis: string[];
  trigger_condition: string;
  measurement_frequency: string;
  approval_status: string;
};

export type KpiTrendsData = {
  items: KpiTrend[];
};

export type GraphData = {
  header: {
    title: string;
    subtitle: string;
  };
  filters: string[];
  map: {
    title: string;
    nodes: SegmentNode[];
    edges?: GraphEdge[];
    stats: string;
  };
  views: GraphView[];
  relation: {
    title: string;
    segment: string;
    evidence: string;
    customers: string;
    hypothesis: string;
    confidence: number;
  };
  lens: KnowledgeLensItem[];
};

export type ReportMessage = {
  id: string;
  role: "assistant" | "user";
  body: string;
  aside?: string;
};

export type ReportData = {
  header: {
    statusLabel: string;
    statusDescription: string;
    title: string;
    subtitle: string;
  };
  topic: string;
  messages: ReportMessage[];
  extraction: {
    title: string;
    observation: string;
    entities: string;
  };
  voiceAction: {
    title: string;
    description: string;
  };
  urlPlaceholder: string;
};

export type ReportCopilotHighlight = {
  id: string;
  kind: "FACT" | "HYPOTHESIS";
  tone: "green" | "yellow";
  title: string;
  description: string;
  meta: string;
};

export type MonthlyReportMetric = {
  id: string;
  label: string;
  value: number;
  unit: string;
  tone: "green" | "yellow" | "blue" | "slate";
};

export type MonthlyReportSection = {
  id: string;
  title: string;
  body: string;
  kind: "summary" | "fact" | "hypothesis";
};

export type ReportCopilotData = {
  header: {
    title: string;
    subtitle: string;
  };
  monthly: {
    title: string;
    period: string;
    summary: string;
    generatedAt: string;
    source: "cloud_storage" | "generated" | "generated_and_saved" | "generated_unsaved";
    storagePath: string;
    gsUri?: string;
  };
  metrics: MonthlyReportMetric[];
  charts: MonthlyReportMetric[];
  sections: MonthlyReportSection[];
  highlights: ReportCopilotHighlight[];
  snippets: string[];
  recommendation: {
    title: string;
    description: string;
    actionLabel: string;
  };
  ctaLabel: string;
};

export const qualityRunSchema = {
  parse<T>(value: T) {
    return value;
  },
};

// Report Chat (アンケート送信フォーム)
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

// Report Copilot (チャット)
export type ChatMessage = {
  role: "user" | "assistant";
  text: string;
};
