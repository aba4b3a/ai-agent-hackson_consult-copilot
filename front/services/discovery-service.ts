import { apiGet, apiPost } from "@/lib/api-client";
import { env } from "@/lib/env";
import {
  type CopilotAnswer,
  copilotAnswerSchema,
  type Dashboard,
  dashboardSchema,
  type EvidenceResult,
  evidenceSearchResponseSchema,
  type GraphSlice,
  graphSliceSchema,
  type WeeklyReport,
  weeklyReportSchema,
  type Workspace,
  workspaceSchema,
} from "@/lib/schemas";
import { discoveryMock } from "@/services/mock/discovery-mock";
import { z } from "zod";

/**
 * Business-logic layer for the Continuous Discovery domain. Routes to local
 * fixtures when env.mockMode is on, otherwise to the backend API (validated
 * against the shared zod schemas). UI hooks depend on this module, never on
 * api-client or the mock directly.
 */

export async function listWorkspaces(): Promise<Workspace[]> {
  if (env.mockMode) return discoveryMock.listWorkspaces();
  return apiGet("/api/workspaces", z.array(workspaceSchema));
}

export async function getDashboard(workspaceId: string): Promise<Dashboard> {
  if (env.mockMode) return discoveryMock.getDashboard();
  return apiGet(`/api/workspaces/${workspaceId}/dashboard`, dashboardSchema);
}

export async function searchEvidence(
  workspaceId: string,
  query: string,
): Promise<EvidenceResult[]> {
  if (env.mockMode) return discoveryMock.searchEvidence(query);
  const params = new URLSearchParams({ workspace_id: workspaceId, q: query });
  const response = await apiGet(
    `/api/search/evidence?${params.toString()}`,
    evidenceSearchResponseSchema,
  );
  return response.results;
}

export async function getGraphSlice(workspaceId: string): Promise<GraphSlice> {
  if (env.mockMode) return discoveryMock.getGraphSlice();
  const params = new URLSearchParams({ workspace_id: workspaceId });
  return apiGet(`/api/graph/slice?${params.toString()}`, graphSliceSchema);
}

export async function getWeeklyReport(workspaceId: string): Promise<WeeklyReport> {
  if (env.mockMode) return discoveryMock.getWeeklyReport();
  const params = new URLSearchParams({ workspace_id: workspaceId });
  return apiGet(`/api/reports/weekly?${params.toString()}`, weeklyReportSchema);
}

export async function askCopilot(
  workspaceId: string,
  question: string,
): Promise<CopilotAnswer> {
  if (env.mockMode) return discoveryMock.askCopilot(question);
  return apiPost(
    "/api/copilot/ask",
    { workspace_id: workspaceId, question },
    copilotAnswerSchema,
  );
}
