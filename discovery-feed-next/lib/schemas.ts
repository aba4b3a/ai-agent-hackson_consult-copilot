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

export type GraphData = {
  header: {
    title: string;
    subtitle: string;
  };
  filters: string[];
  map: {
    title: string;
    nodes: SegmentNode[];
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

export type ReportCopilotData = {
  header: {
    title: string;
    subtitle: string;
  };
  weekly: {
    title: string;
    period: string;
    summary: string;
  };
  highlights: ReportCopilotHighlight[];
  snippets: string[];
  recommendation: {
    title: string;
    description: string;
    actionLabel: string;
  };
  ctaLabel: string;
};
