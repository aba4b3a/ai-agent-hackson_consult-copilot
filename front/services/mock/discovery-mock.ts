import type {
  CopilotAnswer,
  Dashboard,
  EvidenceResult,
  GraphSlice,
  ReportForm,
  ReportFormCreate,
  ReportSubmissionCreate,
  Source,
  VoiceIntakeCreate,
  WeeklyReport,
  Workspace,
  WorkspaceCreate,
} from "@/lib/schemas";

/**
 * Static front-end fixtures so the UI runs end-to-end without a backend
 * (NEXT_PUBLIC_MOCK_MODE=true). Kept consistent with the backend seed in
 * back/app/services/discovery_mock.py (みどり薬局チェーン scenario).
 */

const WORKSPACE_ID = "ws_001";

const workspace: Workspace = {
  workspace_id: WORKSPACE_ID,
  workspace_name: "みどり薬局チェーン",
  business_description: "地域密着型の調剤薬局。処方箋受付、在宅訪問、健康相談を提供。",
  products: ["処方箋受付", "在宅訪問", "健康相談"],
  customer_segments: ["高齢者", "子育て世帯", "慢性疾患患者"],
  competitors: ["駅前ドラッグ", "オンライン服薬指導サービス"],
  known_issues: ["待ち時間", "価格不安", "在庫切れ"],
  kpis: ["再来店率", "待ち時間", "処方箋受付数"],
  observation_topics: ["価格比較", "待ち時間", "オンライン服薬指導への反応"],
  status: "active",
};

const dashboard: Dashboard = {
  workspace,
  metrics: {
    sources_ingested: 18,
    observations_extracted: 42,
    entities_formed: 27,
    hypotheses_under_observation: 3,
    evidence_coverage: 0.86,
  },
  signals: [
    {
      signal_id: "sig_001",
      workspace_id: WORKSPACE_ID,
      signal_type: "weekly_increase",
      metric_name: "competitor_wait_time_mentions",
      current_value: 11,
      baseline_value: 5,
      change_rate: 1.2,
      related_entities: ["待ち時間", "駅前ドラッグ"],
      evidence_count: 4,
      severity: "warning",
    },
    {
      signal_id: "sig_002",
      workspace_id: WORKSPACE_ID,
      signal_type: "new_entity",
      metric_name: "online_consultation_interest",
      current_value: 6,
      baseline_value: 0,
      change_rate: 1,
      related_entities: ["オンライン服薬指導サービス", "子育て世帯"],
      evidence_count: 3,
      severity: "info",
    },
    {
      signal_id: "sig_003",
      workspace_id: WORKSPACE_ID,
      signal_type: "co_occurrence",
      metric_name: "inventory_confirmation_issue",
      current_value: 9,
      baseline_value: 4,
      change_rate: 1.25,
      related_entities: ["在庫切れ", "再来店率"],
      evidence_count: 5,
      severity: "danger",
    },
  ],
  observations: [
    {
      observation_id: "obs_001",
      workspace_id: WORKSPACE_ID,
      source_id: "src_001",
      source_type: "daily_report",
      summary: "高齢者から、競合店の待ち時間が短いという比較発言があった。",
      quote: "駅前ドラッグのほうが待ち時間が短いと言われた。",
      fact_or_hypothesis: "fact",
      confidence: 0.82,
      related_entities: ["高齢者", "待ち時間", "駅前ドラッグ"],
      evidence_uri: "gs://continuous-discovery-local/raw/ws_001/src_001.txt",
    },
    {
      observation_id: "obs_002",
      workspace_id: WORKSPACE_ID,
      source_id: "src_002",
      source_type: "voice_transcript",
      summary: "子育て世帯から、オンライン服薬指導の相談が増えた。",
      quote: "通院後に店舗へ寄る時間が取りづらいそうです。",
      fact_or_hypothesis: "fact",
      confidence: 0.78,
      related_entities: ["子育て世帯", "オンライン服薬指導サービス"],
      evidence_uri: "gs://continuous-discovery-local/raw/ws_001/src_002.txt",
    },
    {
      observation_id: "obs_003",
      workspace_id: WORKSPACE_ID,
      source_id: "src_003",
      source_type: "consultant_note",
      summary: "夕方の在庫確認に時間がかかり、再来店を迷う発言があった。",
      quote: "在庫確認の遅れが再来店意向に影響しているかもしれない。",
      fact_or_hypothesis: "fact",
      confidence: 0.71,
      related_entities: ["在庫切れ", "再来店率"],
      evidence_uri: "gs://continuous-discovery-local/raw/ws_001/src_003.txt",
    },
  ],
  hypotheses: [
    {
      hypothesis_id: "hyp_001",
      workspace_id: WORKSPACE_ID,
      statement: "競合の利便性訴求が、待ち時間への不満を強めている可能性がある。",
      status: "observing",
      confidence: 0.61,
      supporting_observation_ids: ["obs_001"],
      recommended_observations: ["競合名が出た場面で比較理由を確認する"],
    },
    {
      hypothesis_id: "hyp_002",
      workspace_id: WORKSPACE_ID,
      statement: "子育て世帯では、営業時間外の相談手段が継続利用に影響している可能性がある。",
      status: "observing",
      confidence: 0.55,
      supporting_observation_ids: ["obs_002"],
      recommended_observations: ["オンライン服薬指導ニーズを日報で分けて記録する"],
    },
  ],
};

const evidence: EvidenceResult[] = [
  {
    source_id: "src_001",
    observation_id: "obs_001",
    title: "Daily report 2026-06-28",
    source_type: "daily_report",
    snippet: "駅前ドラッグのほうが待ち時間が短いと言われた。",
    tags: ["高齢者", "待ち時間", "駅前ドラッグ"],
    confidence: 0.82,
    evidence_uri: "gs://continuous-discovery-local/raw/ws_001/src_001.txt",
  },
  {
    source_id: "src_002",
    observation_id: "obs_002",
    title: "Voice transcript 2026-06-29",
    source_type: "voice_transcript",
    snippet: "通院後に店舗へ寄る時間が取りづらいそうです。",
    tags: ["子育て世帯", "オンライン服薬指導"],
    confidence: 0.78,
    evidence_uri: "gs://continuous-discovery-local/raw/ws_001/src_002.txt",
  },
  {
    source_id: "src_003",
    observation_id: "obs_003",
    title: "Consultant note 2026-06-30",
    source_type: "consultant_note",
    snippet: "在庫確認の遅れが再来店意向に影響しているかもしれない。",
    tags: ["在庫切れ", "再来店率"],
    confidence: 0.71,
    evidence_uri: "gs://continuous-discovery-local/raw/ws_001/src_003.txt",
  },
];

const graphSlice: GraphSlice = {
  nodes: [
    { id: "seg_elderly", type: "CustomerSegment", label: "高齢者", summary: "主要顧客セグメント" },
    { id: "issue_wait", type: "Issue", label: "待ち時間", summary: "繰り返し観測される課題" },
    { id: "comp_ekimae", type: "Competitor", label: "駅前ドラッグ", summary: "近隣競合" },
    { id: "kpi_return", type: "KPI", label: "再来店率", summary: "固定KPI" },
    { id: "seg_family", type: "CustomerSegment", label: "子育て世帯", summary: "顧客セグメント" },
    { id: "comp_online", type: "Competitor", label: "オンライン服薬指導", summary: "代替サービス競合" },
    { id: "hyp_conv", type: "Hypothesis", label: "競合利便性が不満を強める仮説", summary: "観察中の仮説" },
  ],
  edges: [
    { source: "seg_elderly", target: "issue_wait", type: "MENTIONS", evidence_count: 4, fact_or_hypothesis: "fact" },
    { source: "issue_wait", target: "comp_ekimae", type: "RELATES_TO", evidence_count: 4, fact_or_hypothesis: "fact" },
    { source: "issue_wait", target: "kpi_return", type: "IMPACTS", evidence_count: 3, fact_or_hypothesis: "fact" },
    { source: "seg_family", target: "comp_online", type: "MENTIONS", evidence_count: 3, fact_or_hypothesis: "fact" },
    { source: "hyp_conv", target: "issue_wait", type: "MAY_CAUSE", evidence_count: 2, fact_or_hypothesis: "hypothesis" },
  ],
  summary: "観察事実を中心に、関連エンティティと観察中の仮説を分離して表示しています。",
};

const weeklyReport: WeeklyReport = {
  report_id: "rep_latest",
  workspace_id: WORKSPACE_ID,
  period: "2026-06-23 – 2026-06-29",
  summary:
    "待ち時間と競合利便性に関する言及が増えています。因果は未確定のため、次週も比較理由を重点観察します。",
  observed_facts: dashboard.observations.map((o) => o.summary),
  hypotheses: dashboard.hypotheses.map((h) => h.statement),
  evidence: evidence.slice(0, 3),
  recommended_observations: [
    "競合名が出た発話で、価格・待ち時間・在庫のどれが理由か確認する",
    "子育て世帯のオンライン服薬指導ニーズを日報で分けて記録する",
  ],
  limitations: [
    "デモ用 mock mode のため、BigQuery Graph と Elasticsearch はローカルデータで代替しています。",
    "仮説は観察中であり、確定した事業原因として扱いません。",
  ],
};

function filterEvidence(query: string): EvidenceResult[] {
  const q = query.trim().toLowerCase();
  if (!q) return evidence;
  return evidence.filter((item) =>
    `${item.title} ${item.snippet} ${item.tags.join(" ")}`.toLowerCase().includes(q),
  );
}

/**
 * Synthetic responses for write flows in mock mode. These do NOT persist —
 * front standalone mock stays a read-only preview. Real write E2E runs against
 * back (NEXT_PUBLIC_MOCK_MODE=false). Kept just so the form/chat UIs can show a
 * success state without a backend.
 */
function mockQuestions(focusTopics: string[]): string[] {
  const topics = focusTopics.length > 0 ? focusTopics : ["顧客の変化", "競合名", "業務影響"];
  return [
    "今日、顧客から普段と違う反応や相談はありましたか。",
    `${topics.join("、")}に関係する具体的な発言はありましたか。`,
    "競合名、商品、顧客層、KPIへの影響が分かれば記録してください。",
  ];
}

export const discoveryMock = {
  listWorkspaces(): Workspace[] {
    return [workspace];
  },
  createWorkspace(payload: WorkspaceCreate): Workspace {
    return {
      workspace_id: "ws_mock",
      status: "active",
      workspace_name: payload.workspace_name,
      business_description: payload.business_description ?? "",
      products: payload.products ?? [],
      customer_segments: payload.customer_segments ?? [],
      competitors: payload.competitors ?? [],
      known_issues: payload.known_issues ?? [],
      kpis: payload.kpis ?? [],
      observation_topics: payload.observation_topics ?? [],
    };
  },
  createReportForm(payload: ReportFormCreate): ReportForm {
    const formId = "form_mock";
    return {
      form_id: formId,
      workspace_id: payload.workspace_id,
      url: `/intake?form=${formId}`,
      target_role: payload.target_role ?? "field_staff",
      focus_topics: payload.focus_topics ?? [],
      due_date: payload.due_date ?? null,
      questions: mockQuestions(payload.focus_topics ?? []),
    };
  },
  getReportForm(formId: string): ReportForm {
    return {
      form_id: formId,
      workspace_id: WORKSPACE_ID,
      url: `/intake?form=${formId}`,
      target_role: "field_staff",
      focus_topics: ["価格比較", "待ち時間"],
      due_date: null,
      questions: mockQuestions(["価格比較", "待ち時間"]),
    };
  },
  submitReport(payload: ReportSubmissionCreate): Source {
    return {
      source_id: "src_mock",
      workspace_id: WORKSPACE_ID,
      source_type: "daily_report",
      title: "Daily report (mock)",
      body: payload.free_text,
      processing_status: "extracted",
      source_uri: "gs://continuous-discovery-local/raw/ws_001/src_mock.txt",
    };
  },
  getFollowups(answers: string[]): string[] {
    // Static, policy-aligned follow-ups for offline/demo. Real dynamic
    // generation happens via the agent when NEXT_PUBLIC_MOCK_MODE=false.
    const base = [
      "それは普段と比べてどう違いましたか。原因に心当たりはありますか。",
      "どの顧客層・商品・競合名と関係していましたか。",
      "売上や再来店などの業務への影響につながりそうですか。",
    ];
    return answers.length > 0 ? base : base.slice(0, 2);
  },
  submitVoice(payload: VoiceIntakeCreate): Source {
    return {
      source_id: "src_voice_mock",
      workspace_id: payload.workspace_id,
      source_type: "voice_transcript",
      title: "Voice transcript (mock)",
      body: payload.transcript,
      processing_status: "extracted",
      source_uri: "gs://continuous-discovery-local/raw/ws_001/src_voice_mock.txt",
    };
  },
  getDashboard(): Dashboard {
    return dashboard;
  },
  searchEvidence(query: string): EvidenceResult[] {
    return filterEvidence(query);
  },
  getGraphSlice(): GraphSlice {
    return graphSlice;
  },
  getWeeklyReport(): WeeklyReport {
    return weeklyReport;
  },
  askCopilot(question: string): CopilotAnswer {
    return {
      answer:
        `質問「${question}」について、現時点の観察事実では待ち時間と競合比較の言及が確認できます。` +
        "原因は未確定なので、競合利便性が影響している可能性は仮説として扱い、追加観察で検証してください。",
      observed_facts: weeklyReport.observed_facts,
      hypotheses: weeklyReport.hypotheses,
      evidence: evidence.slice(0, 3),
      recommended_observations: weeklyReport.recommended_observations,
    };
  },
} as const;

export const MOCK_WORKSPACE_ID = WORKSPACE_ID;
