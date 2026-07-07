import { z } from "zod";

// ---------------------------------------------------------------------------
// QualityOps (existing — retained)
// ---------------------------------------------------------------------------

export const qualityRunSchema = z.object({
  quality_run_id: z.string(),
  quality_score: z.number().int().min(0).max(100),
  release_decision: z.enum(["go", "conditional_go", "no_go"]),
  risk_level: z.enum(["low", "medium", "high"]),
});

export type QualityRun = z.infer<typeof qualityRunSchema>;

// ---------------------------------------------------------------------------
// Continuous Discovery domain
// Mirrors back/app/schemas/discovery.py — BigQuery is the source of truth; the
// backend is the contract these schemas validate against.
// ---------------------------------------------------------------------------

export const workspaceSchema = z.object({
  workspace_id: z.string(),
  workspace_name: z.string(),
  business_description: z.string().default(""),
  products: z.array(z.string()).default([]),
  customer_segments: z.array(z.string()).default([]),
  competitors: z.array(z.string()).default([]),
  known_issues: z.array(z.string()).default([]),
  kpis: z.array(z.string()).default([]),
  observation_topics: z.array(z.string()).default([]),
  status: z.string().default("active"),
});
export type Workspace = z.infer<typeof workspaceSchema>;

export const sourceSchema = z.object({
  source_id: z.string(),
  workspace_id: z.string(),
  source_type: z.string(),
  title: z.string(),
  body: z.string(),
  processing_status: z.string(),
  source_uri: z.string(),
});
export type Source = z.infer<typeof sourceSchema>;

export const observationSchema = z.object({
  observation_id: z.string(),
  workspace_id: z.string(),
  source_id: z.string(),
  source_type: z.string(),
  observed_at: z.string().optional(),
  summary: z.string(),
  quote: z.string(),
  fact_or_hypothesis: z.string().default("fact"),
  confidence: z.number(),
  related_entities: z.array(z.string()),
  evidence_uri: z.string(),
});
export type Observation = z.infer<typeof observationSchema>;

export const hypothesisSchema = z.object({
  hypothesis_id: z.string(),
  workspace_id: z.string(),
  statement: z.string(),
  status: z.string(),
  confidence: z.number(),
  supporting_observation_ids: z.array(z.string()),
  recommended_observations: z.array(z.string()),
});
export type Hypothesis = z.infer<typeof hypothesisSchema>;

export const discoverySignalSchema = z.object({
  signal_id: z.string(),
  workspace_id: z.string(),
  signal_type: z.string(),
  metric_name: z.string(),
  current_value: z.number(),
  baseline_value: z.number(),
  change_rate: z.number(),
  related_entities: z.array(z.string()),
  evidence_count: z.number().int(),
  severity: z.string(),
});
export type DiscoverySignal = z.infer<typeof discoverySignalSchema>;

export const evidenceResultSchema = z.object({
  source_id: z.string(),
  observation_id: z.string().nullable().optional(),
  title: z.string(),
  source_type: z.string(),
  snippet: z.string(),
  tags: z.array(z.string()),
  confidence: z.number(),
  evidence_uri: z.string(),
});
export type EvidenceResult = z.infer<typeof evidenceResultSchema>;

export const graphNodeSchema = z.object({
  id: z.string(),
  type: z.string(),
  label: z.string(),
  summary: z.string(),
});
export type GraphNode = z.infer<typeof graphNodeSchema>;

export const graphEdgeSchema = z.object({
  source: z.string(),
  target: z.string(),
  type: z.string(),
  evidence_count: z.number().int(),
  fact_or_hypothesis: z.string(),
});
export type GraphEdge = z.infer<typeof graphEdgeSchema>;

export const graphSliceSchema = z.object({
  nodes: z.array(graphNodeSchema),
  edges: z.array(graphEdgeSchema),
  summary: z.string(),
});
export type GraphSlice = z.infer<typeof graphSliceSchema>;

export const weeklyReportSchema = z.object({
  report_id: z.string(),
  workspace_id: z.string(),
  period: z.string(),
  summary: z.string(),
  observed_facts: z.array(z.string()),
  hypotheses: z.array(z.string()),
  evidence: z.array(evidenceResultSchema),
  recommended_observations: z.array(z.string()),
  limitations: z.array(z.string()),
});
export type WeeklyReport = z.infer<typeof weeklyReportSchema>;

export const copilotAnswerSchema = z.object({
  answer: z.string(),
  observed_facts: z.array(z.string()),
  hypotheses: z.array(z.string()),
  evidence: z.array(evidenceResultSchema),
  recommended_observations: z.array(z.string()),
});
export type CopilotAnswer = z.infer<typeof copilotAnswerSchema>;

export const dashboardMetricsSchema = z.object({
  sources_ingested: z.number(),
  observations_extracted: z.number(),
  entities_formed: z.number(),
  relationships_created: z.number(),
  hypotheses_under_observation: z.number(),
  evidence_coverage: z.number(),
});
export type DashboardMetrics = z.infer<typeof dashboardMetricsSchema>;

export const dashboardSchema = z.object({
  workspace: workspaceSchema,
  metrics: dashboardMetricsSchema,
  signals: z.array(discoverySignalSchema),
  observations: z.array(observationSchema),
  hypotheses: z.array(hypothesisSchema),
});
export type Dashboard = z.infer<typeof dashboardSchema>;

export const evidenceSearchResponseSchema = z.object({
  results: z.array(evidenceResultSchema),
});
export type EvidenceSearchResponse = z.infer<typeof evidenceSearchResponseSchema>;

// ---------------------------------------------------------------------------
// Intake request / response payloads (M2)
// Mirrors the *Create request models in back/app/schemas/discovery.py.
// ---------------------------------------------------------------------------

export const workspaceCreateSchema = z.object({
  workspace_name: z.string().min(1),
  business_description: z.string().default(""),
  products: z.array(z.string()).default([]),
  customer_segments: z.array(z.string()).default([]),
  competitors: z.array(z.string()).default([]),
  known_issues: z.array(z.string()).default([]),
  kpis: z.array(z.string()).default([]),
  observation_topics: z.array(z.string()).default([]),
});
export type WorkspaceCreate = z.input<typeof workspaceCreateSchema>;

export const reportFormCreateSchema = z.object({
  workspace_id: z.string(),
  target_role: z.string().default("field_staff"),
  focus_topics: z.array(z.string()).default([]),
  due_date: z.string().nullable().optional(),
});
export type ReportFormCreate = z.input<typeof reportFormCreateSchema>;

export const reportFormSchema = z.object({
  form_id: z.string(),
  workspace_id: z.string(),
  url: z.string(),
  target_role: z.string(),
  focus_topics: z.array(z.string()),
  due_date: z.string().nullable().optional(),
  questions: z.array(z.string()),
});
export type ReportForm = z.infer<typeof reportFormSchema>;

export const reportSubmissionCreateSchema = z.object({
  form_id: z.string(),
  submitted_by_role: z.string().default("field_staff"),
  free_text: z.string(),
  customer_type: z.string().default("unknown"),
  product: z.string().default("unknown"),
  issue_category: z.string().default("unknown"),
  competitor: z.string().nullable().optional(),
  kpi_note: z.string().nullable().optional(),
});
export type ReportSubmissionCreate = z.input<typeof reportSubmissionCreateSchema>;

export const voiceIntakeCreateSchema = z.object({
  workspace_id: z.string(),
  submitted_by_role: z.string().default("field_staff"),
  transcript: z.string(),
});
export type VoiceIntakeCreate = z.input<typeof voiceIntakeCreateSchema>;

export const followupResponseSchema = z.object({
  questions: z.array(z.string()),
});
export type FollowupResponse = z.infer<typeof followupResponseSchema>;
