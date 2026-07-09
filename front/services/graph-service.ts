import { apiFetch, companyId } from "@/lib/api-client";

// design §10.4 Graph Slice API のレスポンス型
export type SliceNode = {
  node_id: string;
  node_type: string;
  label: string | null;
  description: string | null;
  confidence: number | null;
  status: string | null;
};

export type SliceEdge = {
  source_node_id: string;
  target_node_id: string;
  edge_type: string;
  strength: number | null;
  observed_count: number | null;
  description: string | null;
};

export type GraphSliceResponse = {
  nodes: SliceNode[];
  edges: SliceEdge[];
  meta: {
    truncated: boolean;
    center_node_id: string | null;
    period: string;
    source: "bigquery" | "sample";
  };
};

export const getGraphSlice = (targetCompanyId = companyId): Promise<GraphSliceResponse> =>
  apiFetch(`/api/v1/companies/${encodeURIComponent(targetCompanyId)}/graph/slice?limit=50`);
