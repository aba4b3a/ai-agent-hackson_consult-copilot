import type { GraphSliceResponse, SliceEdge, SliceNode } from "@/services/graph-service";
import type { GraphData, GraphEdge, GraphView, SegmentNode } from "@/lib/schemas";

// design §10.1 の10ノード型に対応（back の tone_map と同義）
const nodeToneMap: Record<string, SegmentNode["tone"]> = {
  Signal: "rose",
  Risk: "rose",
  KPI: "amber",
  TacitKnowledge: "violet",
  ProductService: "violet",
  CompanyProfile: "cyan",
  CustomerSegment: "cyan",
  Person: "cyan",
  Process: "blue",
  ResearchPolicy: "blue",
};

const nodeSizeMap: Record<string, SegmentNode["size"]> = {
  CompanyProfile: "lg",
  ResearchPolicy: "lg",
  KPI: "md",
  Signal: "md",
};

// design §10.2 の7関係型に対応
const edgeToneMap: Record<string, GraphEdge["tone"]> = {
  LEADING_INDICATOR_OF: "rose",
  PRESSURES: "rose",
  PROTECTS: "violet",
  KNOWS: "violet",
  DRIVES: "blue",
  OBSERVES: "blue",
  CREATES: "amber",
};

const viewTones: GraphView["tone"][] = ["yellow", "green", "purple", "blue"];

const isHypothesis = (edgeType: string) => edgeType === "LEADING_INDICATOR_OF";

const topNodeTypes = (nodes: SliceNode[], limit: number): string[] => {
  const counts = new Map<string, number>();
  nodes.forEach((node) => counts.set(node.node_type, (counts.get(node.node_type) ?? 0) + 1));
  return [...counts.entries()].sort((a, b) => b[1] - a[1]).slice(0, limit).map(([type]) => type);
};

const toSegmentNode = (node: SliceNode): SegmentNode => ({
  id: node.node_id,
  label: node.label ?? node.node_type,
  tone: nodeToneMap[node.node_type] ?? "blue",
  position: "center", // レイアウトは KnowledgeGraph 側の buildClusteredLayout が計算する
  nodeType: node.node_type,
  description: node.description ?? undefined,
  size: nodeSizeMap[node.node_type] ?? "sm",
  meta: node.node_type,
});

const toGraphEdge = (edge: SliceEdge, index: number): GraphEdge => ({
  id: `${edge.source_node_id}-${edge.target_node_id}-${edge.edge_type}-${index}`,
  source: edge.source_node_id,
  target: edge.target_node_id,
  label: edge.edge_type,
  tone: edgeToneMap[edge.edge_type] ?? "slate",
  strength: Math.max(0.2, Math.min(1.0, edge.strength ?? 0.55)),
  description: edge.description ?? undefined,
  hypothesis: isHypothesis(edge.edge_type),
});

// slice レスポンス（design §10.4）を既存グラフ画面の表示モデルへ変換する
export const sliceToGraphData = (slice: GraphSliceResponse): GraphData => {
  const nodes = slice.nodes.map(toSegmentNode);
  const edges = slice.edges.map(toGraphEdge);
  const types = topNodeTypes(slice.nodes, 4);
  const hypothesisCount = edges.filter((edge) => edge.hypothesis).length;
  const factCount = edges.length - hypothesisCount;
  const topEdge = [...edges].sort((a, b) => b.strength - a.strength)[0];

  return {
    header: {
      title: "Knowledge Graph",
      subtitle: slice.meta.source === "bigquery" ? "BigQuery 実データ" : "サンプルデータ（seed）",
    },
    filters: ["全て", ...types],
    map: {
      title: "Knowledge Map",
      nodes,
      edges,
      stats: `Nodes ${nodes.length} / Relations ${edges.length}${slice.meta.truncated ? "（上限で切り詰め）" : ""}`,
    },
    views: types.map((type, index) => ({
      id: `view-${type}`,
      label: type,
      tone: viewTones[index % viewTones.length],
    })),
    relation: {
      title: "Selected relation",
      segment: topEdge?.label ?? "データなし",
      evidence: topEdge?.description ?? "関係の説明はまだありません",
      customers: "",
      hypothesis: topEdge?.hypothesis ? "この関係は仮説（先行指標の可能性）です" : "",
      confidence: Math.round((topEdge?.strength ?? 0.5) * 100),
    },
    lens: [
      { id: "l1", label: "Fact graph", value: `観測された関係 ${factCount} 件` },
      { id: "l2", label: "Hypothesis graph", value: `仮説の関係（破線） ${hypothesisCount} 件` },
      { id: "l3", label: "Nodes", value: `${nodes.length} 件（${types.join(" / ")}）` },
    ],
  };
};
