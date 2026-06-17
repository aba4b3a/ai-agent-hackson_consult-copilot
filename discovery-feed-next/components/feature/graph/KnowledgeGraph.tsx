"use client";

import { BottomNav } from "@/components/feature/discovery/BottomNav";
import { PhoneFrame } from "@/components/ui/PhoneFrame";
import { SectionTitle } from "@/components/ui/SectionTitle";
import { useGraph } from "@/hooks/use-graph";
import type { GraphView, SegmentNode } from "@/lib/schemas";

const nodeToneClass: Record<SegmentNode["tone"], string> = {
  rose: "bg-rose-100 text-rose-400",
  cyan: "bg-cyan-100 text-cyan-500",
  amber: "bg-amber-100 text-amber-500",
  violet: "bg-violet-100 text-violet-500",
  blue: "bg-blue-600 text-white",
};

const nodePositionClass: Record<SegmentNode["position"], string> = {
  topLeft: "left-[22%] top-[14%]",
  topRight: "right-[20%] top-[16%]",
  bottomLeft: "left-[20%] bottom-[16%]",
  bottomRight: "right-[19%] bottom-[15%]",
  center: "left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2",
};

const viewToneClass: Record<GraphView["tone"], string> = {
  blue: "bg-blue-100 text-blue-700",
  green: "bg-emerald-100 text-emerald-700",
  yellow: "bg-amber-100 text-amber-700",
  purple: "bg-violet-100 text-violet-700",
};

const Card = ({ children, className = "" }: { children: React.ReactNode; className?: string }) => {
  return <section className={`rounded-[22px] bg-white p-4 shadow-[0_12px_28px_rgba(15,23,42,0.05)] ${className}`}>{children}</section>;
};

const LoadingState = ({ message }: { message: string }) => (
  <PhoneFrame>
    <div className="flex min-h-screen items-center justify-center px-6 text-center text-sm font-bold text-slate-500 md:min-h-[720px]">{message}</div>
  </PhoneFrame>
);

export const KnowledgeGraph = () => {
  const { data, isLoading, isError } = useGraph();

  if (isLoading) return <LoadingState message="Loading..." />;
  if (isError || !data) return <LoadingState message="データの取得に失敗しました。" />;

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
          <div className="relative mx-auto mt-3 h-44 max-w-[280px]">
            <svg className="absolute inset-0 h-full w-full" viewBox="0 0 280 176" aria-hidden="true">
              <line x1="140" y1="88" x2="78" y2="42" stroke="#dbeafe" strokeWidth="7" strokeLinecap="round" />
              <line x1="140" y1="88" x2="205" y2="43" stroke="#dbeafe" strokeWidth="7" strokeLinecap="round" />
              <line x1="140" y1="88" x2="78" y2="133" stroke="#dbeafe" strokeWidth="7" strokeLinecap="round" />
              <line x1="140" y1="88" x2="205" y2="132" stroke="#dbeafe" strokeWidth="7" strokeLinecap="round" />
            </svg>
            {data.map.nodes.map((node) => (
              <div
                key={node.id}
                className={`absolute grid place-items-center whitespace-pre-line rounded-full text-center text-[10px] font-black leading-tight md:text-xs ${node.position === "center" ? "h-16 w-16" : "h-14 w-14"} ${nodeToneClass[node.tone]} ${nodePositionClass[node.position]}`}
              >
                {node.label}
              </div>
            ))}
          </div>
          <p className="mt-1 text-[10px] font-extrabold text-blue-400 md:text-xs">{data.map.stats}</p>
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
