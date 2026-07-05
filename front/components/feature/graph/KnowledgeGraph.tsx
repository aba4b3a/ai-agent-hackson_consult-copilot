"use client";

import { BottomNav } from "@/components/feature/discovery/BottomNav";
import { Card } from "@/components/ui/Card";
import { LoadingState } from "@/components/ui/LoadingState";
import { PhoneFrame } from "@/components/ui/PhoneFrame";
import { SectionTitle } from "@/components/ui/SectionTitle";
import { useGraph } from "@/hooks/use-graph";
import type { GraphEdge, GraphView, SegmentNode } from "@/lib/schemas";

const nodeToneClass: Record<SegmentNode["tone"], string> = {
  rose: "bg-rose-100 text-rose-500",
  cyan: "bg-cyan-100 text-cyan-600",
  amber: "bg-amber-100 text-amber-600",
  violet: "bg-violet-100 text-violet-600",
  blue: "bg-blue-600 text-white",
};

const nodePositionClass: Record<SegmentNode["position"], string> = {
  topLeft: "left-[23%] top-[20%]",
  topRight: "right-[23%] top-[20%]",
  bottomLeft: "left-[24%] bottom-[20%]",
  bottomRight: "right-[23%] bottom-[20%]",
  center: "left-1/2 top-1/2",
};

const fallbackPosition: Record<SegmentNode["position"], { x: number; y: number }> = {
  topLeft: { x: 84, y: 52 },
  topRight: { x: 276, y: 54 },
  bottomLeft: { x: 88, y: 206 },
  bottomRight: { x: 272, y: 204 },
  center: { x: 180, y: 130 },
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

const getPoint = (node: SegmentNode) => ({
  x: node.x ?? fallbackPosition[node.position].x,
  y: node.y ?? fallbackPosition[node.position].y,
});

export const KnowledgeGraph = () => {
  const { data, isLoading, isError } = useGraph();

  if (isLoading) return <LoadingState message="Loading..." />;
  if (isError || !data) return <LoadingState message="データの取得に失敗しました。" />;

  const nodes = data.map.nodes.slice(0, 14);
  const nodeById = new Map(nodes.map((node) => [node.id, node]));
  const edges = (data.map.edges ?? []).filter((edge) => nodeById.has(edge.source) && nodeById.has(edge.target)).slice(0, 18);

  return (
    <PhoneFrame>
      <div className="px-5 pb-24 pt-5 md:px-7 md:pb-8 md:pt-8">
        <header>
          <h1 className="text-[20px] font-black tracking-tight text-slate-950 md:text-2xl">{data.header.title}</h1>
          <p className="mt-1 text-[11px] font-extrabold text-slate-500 md:text-sm">{data.header.subtitle}</p>
        </header>

        <div className="mt-4 flex gap-2 overflow-x-auto pb-1 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
          {data.filters.map((filter, index) => (
            <button
              key={filter}
              className={`shrink-0 rounded-full px-4 py-2 text-[10px] font-black md:text-xs ${index === 0 ? "bg-blue-100 text-blue-700" : "bg-white text-slate-500 shadow-[0_8px_18px_rgba(15,23,42,0.04)]"}`}
              type="button"
            >
              {filter}
            </button>
          ))}
        </div>

        <Card className="mt-3">
          <SectionTitle>{data.map.title}</SectionTitle>
          <div className="relative mx-auto mt-3 aspect-[18/13] max-w-[360px] overflow-hidden rounded-[8px] bg-slate-50 ring-1 ring-slate-100">
            <svg className="absolute inset-0 h-full w-full" viewBox="0 0 360 260" aria-hidden="true">
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
                  className={`absolute -translate-x-1/2 -translate-y-1/2 rounded-[8px] px-2 py-1.5 text-center shadow-sm ring-1 ring-white/80 ${nodeSizeClass} ${nodeToneClass[node.tone]} ${node.x === undefined && node.y === undefined ? nodePositionClass[node.position] : ""}`}
                  style={node.x !== undefined || node.y !== undefined ? { left: `${(point.x / 360) * 100}%`, top: `${(point.y / 260) * 100}%` } : undefined}
                  title={node.description}
                >
                  <p className="truncate text-[9px] font-black leading-tight md:text-[10px]">{node.label}</p>
                  <p className="mt-0.5 truncate text-[8px] font-extrabold opacity-70">{node.meta ?? node.nodeType}</p>
                </div>
              );
            })}
          </div>
          <p className="mt-1 text-[10px] font-extrabold text-blue-400 md:text-xs">{data.map.stats}</p>
          {edges.length > 0 && (
            <div className="mt-3 grid grid-cols-1 gap-2 md:grid-cols-2">
              {edges.slice(0, 6).map((edge) => (
                <div key={edge.id} className="rounded-[8px] bg-white px-3 py-2 ring-1 ring-slate-100">
                  <div className="flex items-center justify-between gap-2">
                    <span className={`min-w-0 truncate rounded-full px-2 py-1 text-[9px] font-black ${edgeLabelToneClass[edge.tone]}`}>{edge.label}</span>
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
              <button key={view.id} type="button" className={`rounded-full px-2 py-2 text-[9px] font-black md:text-[11px] ${viewToneClass[view.tone]}`}>
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
      <BottomNav active="graph" />
    </PhoneFrame>
  );
};
