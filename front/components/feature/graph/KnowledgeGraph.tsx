"use client";

import { useMemo, useState } from "react";
import { Card } from "@/components/ui/Card";
import { SectionTitle } from "@/components/ui/SectionTitle";
import { useGraph } from "@/hooks/use-graph";
import type { GraphEdge, GraphView, SegmentNode } from "@/lib/schemas";

const MAP_WIDTH = 360;
const MAP_HEIGHT = 260;

const nodeToneClass: Record<SegmentNode["tone"], string> = {
  rose: "bg-rose-100 text-rose-500",
  cyan: "bg-cyan-100 text-cyan-600",
  amber: "bg-amber-100 text-amber-600",
  violet: "bg-violet-100 text-violet-600",
  blue: "bg-blue-600 text-white",
};

const clusterToneClass: Record<SegmentNode["tone"], string> = {
  rose: "bg-rose-50/80 ring-rose-100",
  cyan: "bg-cyan-50/80 ring-cyan-100",
  amber: "bg-amber-50/80 ring-amber-100",
  violet: "bg-violet-50/80 ring-violet-100",
  blue: "bg-blue-50/80 ring-blue-100",
};

const categoryOf = (node: SegmentNode) => node.nodeType || node.meta || "Other";

type ClusterLayout = {
  points: Map<string, { x: number; y: number }>;
  clusters: { key: string; tone: SegmentNode["tone"]; x: number; y: number; width: number; height: number }[];
};

// Groups nodes by category (nodeType/meta) into a grid of cells instead of
// relying on the arbitrary per-index position/x/y the API sends.
const buildClusteredLayout = (nodes: SegmentNode[]): ClusterLayout => {
  const order: string[] = [];
  const groups = new Map<string, SegmentNode[]>();
  nodes.forEach((node) => {
    const key = categoryOf(node);
    if (!groups.has(key)) {
      groups.set(key, []);
      order.push(key);
    }
    groups.get(key)!.push(node);
  });

  const cols = Math.max(1, Math.ceil(Math.sqrt(order.length)));
  const rows = Math.max(1, Math.ceil(order.length / cols));
  const cellW = MAP_WIDTH / cols;
  const cellH = MAP_HEIGHT / rows;

  const points = new Map<string, { x: number; y: number }>();
  const clusters: ClusterLayout["clusters"] = [];

  order.forEach((key, ci) => {
    const col = ci % cols;
    const row = Math.floor(ci / cols);
    const cellX = col * cellW;
    const cellY = row * cellH;
    const labelGutter = 14;
    const innerX = cellX + 8;
    const innerY = cellY + labelGutter;
    const innerW = cellW - 16;
    const innerH = cellH - labelGutter - 8;

    const members = groups.get(key)!;
    const subCols = Math.max(1, Math.ceil(Math.sqrt(members.length)));
    const subRows = Math.max(1, Math.ceil(members.length / subCols));
    members.forEach((node, ni) => {
      const sc = ni % subCols;
      const sr = Math.floor(ni / subCols);
      points.set(node.id, {
        x: innerX + ((sc + 0.5) * innerW) / subCols,
        y: innerY + ((sr + 0.5) * innerH) / subRows,
      });
    });

    clusters.push({ key, tone: members[0].tone, x: cellX + 4, y: cellY + 4, width: cellW - 8, height: cellH - 8 });
  });

  return { points, clusters };
};

const viewToneClass: Record<GraphView["tone"], string> = {
  blue: "bg-blue-100 text-blue-700",
  green: "bg-emerald-100 text-emerald-700",
  yellow: "bg-amber-100 text-amber-700",
  purple: "bg-violet-100 text-violet-700",
};

const edgeToneClass: Record<GraphEdge["tone"], string> = {
  blue: "stroke-blue-200",
  rose: "stroke-rose-200",
  amber: "stroke-amber-200",
  violet: "stroke-violet-200",
  slate: "stroke-slate-200",
};

const edgeLabelToneClass: Record<GraphEdge["tone"], string> = {
  blue: "bg-blue-50 text-blue-700",
  rose: "bg-rose-50 text-rose-700",
  amber: "bg-amber-50 text-amber-700",
  violet: "bg-violet-50 text-violet-700",
  slate: "bg-slate-100 text-slate-600",
};

export const KnowledgeGraphSection = () => {
  const { data, isLoading, isError } = useGraph();
  const [activeFilterIndex, setActiveFilterIndex] = useState(0);
  const [activeViewId, setActiveViewId] = useState<string | null>(null);

  const nodes = useMemo(() => {
    const allNodes = data?.map.nodes ?? [];
    const activeFilter = data?.filters[activeFilterIndex];
    const isAllFilter = activeFilterIndex === 0 || !activeFilter;
    const activeView = data?.views.find((view) => view.id === activeViewId);

    return allNodes
      .filter((node) => {
        if (isAllFilter) return true;
        const haystack = [node.label, node.description, node.meta, node.nodeType].filter(Boolean).join(" ").toLowerCase();
        return haystack.includes(activeFilter.toLowerCase());
      })
      .filter((node) => {
        if (!activeView) return true;
        return (node.nodeType ?? node.meta ?? "").toLowerCase().includes(activeView.label.toLowerCase());
      })
      .slice(0, 14);
  }, [data, activeFilterIndex, activeViewId]);
  const { points, clusters } = useMemo(() => buildClusteredLayout(nodes), [nodes]);
  const getPoint = (node: SegmentNode) => points.get(node.id) ?? { x: MAP_WIDTH / 2, y: MAP_HEIGHT / 2 };

  if (isLoading) {
    return <p className="rounded-lg bg-white px-4 py-6 text-center text-sm font-bold text-slate-500 shadow-[0_10px_24px_rgba(15,23,42,0.04)]">Loading...</p>;
  }
  if (isError || !data) {
    return <p className="rounded-lg bg-white px-4 py-6 text-center text-sm font-bold text-rose-500 shadow-[0_10px_24px_rgba(15,23,42,0.04)]">データの取得に失敗しました。</p>;
  }

  const nodeById = new Map(nodes.map((node) => [node.id, node]));
  const edges = (data.map.edges ?? []).filter((edge) => nodeById.has(edge.source) && nodeById.has(edge.target)).slice(0, 18);

  return (
    <div className="space-y-3">
        <header>
          <h1 className="text-[20px] font-black tracking-tight text-slate-950 md:text-2xl">{data.header.title}</h1>
          <p className="mt-1 text-[11px] font-extrabold text-slate-500 md:text-sm">{data.header.subtitle}</p>
        </header>

        <div className="mt-4 flex gap-2 overflow-x-auto pb-1 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
          {data.filters.map((filter, index) => (
            <button
              key={filter}
              onClick={() => setActiveFilterIndex(index)}
              className={`shrink-0 rounded-full px-4 py-2 text-[10px] font-black transition-colors md:text-xs ${index === activeFilterIndex ? "bg-blue-100 text-blue-700" : "bg-white text-slate-500 shadow-[0_8px_18px_rgba(15,23,42,0.04)]"}`}
              type="button"
            >
              {filter}
            </button>
          ))}
        </div>

        <Card className="mt-3">
          <SectionTitle>{data.map.title}</SectionTitle>
          <div className="relative mx-auto mt-3 aspect-[18/13] w-full max-w-[360px] overflow-hidden rounded-[8px] bg-slate-50 ring-1 ring-slate-100 md:max-w-none">
            {clusters.map((cluster) => (
              <div
                key={cluster.key}
                className={`absolute rounded-[8px] ring-1 ${clusterToneClass[cluster.tone]}`}
                style={{
                  left: `${(cluster.x / MAP_WIDTH) * 100}%`,
                  top: `${(cluster.y / MAP_HEIGHT) * 100}%`,
                  width: `${(cluster.width / MAP_WIDTH) * 100}%`,
                  height: `${(cluster.height / MAP_HEIGHT) * 100}%`,
                }}
              >
                <span title={cluster.key} className="absolute left-1.5 top-1 max-w-[calc(100%-8px)] truncate text-[7px] font-black uppercase tracking-wide text-slate-400">
                  {cluster.key}
                </span>
              </div>
            ))}
            <svg className="absolute inset-0 h-full w-full" viewBox={`0 0 ${MAP_WIDTH} ${MAP_HEIGHT}`} aria-hidden="true">
              {edges.map((edge) => {
                const source = nodeById.get(edge.source);
                const target = nodeById.get(edge.target);
                if (!source || !target) return null;
                const sourcePoint = getPoint(source);
                const targetPoint = getPoint(target);

                return (
                  <line
                    key={edge.id}
                    x1={sourcePoint.x}
                    y1={sourcePoint.y}
                    x2={targetPoint.x}
                    y2={targetPoint.y}
                    className={edgeToneClass[edge.tone]}
                    strokeWidth={Math.max(2, Math.round(edge.strength * 7))}
                    strokeLinecap="round"
                    strokeDasharray={edge.hypothesis ? "6 4" : undefined}
                  />
                );
              })}
            </svg>
            {nodes.map((node) => {
              const point = getPoint(node);
              const nodeSizeClass = node.size === "lg" ? "w-[92px]" : node.size === "sm" ? "w-[68px]" : "w-[78px]";

              return (
                <div
                  key={node.id}
                  className={`absolute -translate-x-1/2 -translate-y-1/2 rounded-[8px] px-2 py-1.5 text-center shadow-sm ring-1 ring-white/80 ${nodeSizeClass} ${nodeToneClass[node.tone]}`}
                  style={{ left: `${(point.x / MAP_WIDTH) * 100}%`, top: `${(point.y / MAP_HEIGHT) * 100}%` }}
                  title={node.description}
                >
                  <p title={node.label} className="truncate text-[9px] font-black leading-tight md:text-[10px]">{node.label}</p>
                  <p title={node.meta ?? node.nodeType} className="mt-0.5 truncate text-[8px] font-extrabold opacity-70">{node.meta ?? node.nodeType}</p>
                </div>
              );
            })}
            {nodes.length === 0 && (
              <p className="absolute inset-0 flex items-center justify-center px-4 text-center text-[10px] font-extrabold text-slate-400">該当するノードがありません</p>
            )}
          </div>
          <p className="mt-1 text-[10px] font-extrabold text-blue-400 md:text-xs">{data.map.stats}</p>
          {edges.length > 0 && (
            <div className="mt-3 grid grid-cols-1 gap-2 md:grid-cols-2">
              {edges.slice(0, 6).map((edge) => (
                <div key={edge.id} className="rounded-[8px] bg-white px-3 py-2 ring-1 ring-slate-100">
                  <div className="flex items-center justify-between gap-2">
                    <span title={edge.label} className={`min-w-0 truncate rounded-full px-2 py-1 text-[9px] font-black ${edgeLabelToneClass[edge.tone]}`}>{edge.label}</span>
                    <span className="shrink-0 text-[9px] font-extrabold text-slate-400">{Math.round(edge.strength * 100)}%</span>
                  </div>
                  {edge.description && <p className="mt-1 line-clamp-2 text-[10px] font-bold leading-relaxed text-slate-500">{edge.description}</p>}
                </div>
              ))}
            </div>
          )}
        </Card>

        <Card className="mt-3">
          <SectionTitle>Graph Views</SectionTitle>
          <div className="mt-3 grid grid-cols-4 gap-2">
            {data.views.map((view) => (
              <button
                key={view.id}
                type="button"
                onClick={() => setActiveViewId((current) => (current === view.id ? null : view.id))}
                className={`rounded-full px-2 py-2 text-[9px] font-black transition-shadow md:text-[11px] ${viewToneClass[view.tone]} ${activeViewId === view.id ? "ring-2 ring-offset-1 ring-current" : "opacity-80"}`}
              >
                {view.label}
              </button>
            ))}
          </div>
        </Card>

        <Card className="mt-3">
          <SectionTitle>{data.relation.title}</SectionTitle>
          <p className="mt-2 text-[11px] font-black leading-relaxed text-slate-800 md:text-sm">{data.relation.segment}</p>
          <div className="mt-3 space-y-1.5">
            <p className="text-[10px] font-extrabold text-slate-500 md:text-xs">{data.relation.evidence}</p>
            <p className="text-[10px] font-extrabold text-slate-500 md:text-xs">{data.relation.hypothesis}</p>
          </div>
          <div className="mt-3 h-2 rounded-full bg-slate-100">
            <div className="h-full rounded-full bg-blue-500" style={{ width: `${data.relation.confidence}%` }} />
          </div>
        </Card>

        <Card className="mt-3">
          <SectionTitle>Knowledge Lens</SectionTitle>
          <dl className="mt-3 space-y-2">
            {data.lens.map((item) => (
              <div key={item.id} className="flex gap-1 text-[11px] font-extrabold leading-relaxed md:text-sm">
                <dt className="shrink-0 text-slate-950">{item.label}:</dt>
                <dd className="text-slate-600">{item.value}</dd>
              </div>
            ))}
          </dl>
        </Card>
    </div>
  );
};
