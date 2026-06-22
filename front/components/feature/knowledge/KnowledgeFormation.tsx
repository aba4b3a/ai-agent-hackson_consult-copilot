"use client";

import { BottomNav } from "@/components/feature/discovery/BottomNav";
import { Card } from "@/components/ui/Card";
import { LoadingState } from "@/components/ui/LoadingState";
import { PhoneFrame } from "@/components/ui/PhoneFrame";
import { SectionTitle } from "@/components/ui/SectionTitle";
import { useKnowledge } from "@/hooks/use-knowledge";
import type { GapTag, KnowledgeMetric, PipelineItem } from "@/lib/schemas";

const metricToneClass: Record<KnowledgeMetric["tone"], string> = {
  blue: "bg-blue-100 text-blue-700",
  green: "bg-emerald-100 text-emerald-700",
  yellow: "bg-amber-100 text-amber-700",
  purple: "bg-violet-100 text-violet-700",
};

const pipelineToneClass: Record<PipelineItem["tone"], string> = {
  blue: "bg-blue-600",
  teal: "bg-teal-500",
  amber: "bg-amber-500",
};

const gapToneClass: Record<GapTag["tone"], string> = {
  rose: "bg-rose-100 text-rose-600",
  blue: "bg-blue-100 text-blue-600",
};

export const KnowledgeFormation = () => {
  const { data, isLoading, isError } = useKnowledge();

  if (isLoading) {
    return (
      <PhoneFrame>
        <div className="flex min-h-screen items-center justify-center text-sm font-bold text-slate-500 md:min-h-[720px]">Loading...</div>
      </PhoneFrame>
    );
  }

  if (isError || !data) {
    return (
      <PhoneFrame>
        <div className="flex min-h-screen items-center justify-center px-6 text-center text-sm font-bold text-rose-500 md:min-h-[720px]">
          データの取得に失敗しました。
        </div>
      </PhoneFrame>
    );
  }

  return (
    <PhoneFrame>
      <div className="px-5 pb-24 pt-5 md:px-7 md:pb-8 md:pt-8">
        <header className="flex items-center justify-between rounded-full bg-white px-2.5 py-2 shadow-[0_10px_24px_rgba(15,23,42,0.04)]">
          <div className="flex items-center gap-2">
            <div className="h-7 w-7 rounded-full bg-gradient-to-br from-emerald-300 to-teal-600" />
            <div>
              <p className="text-[10px] font-extrabold text-emerald-700 md:text-xs">{data.header.statusLabel}</p>
              <p className="text-[8px] font-semibold text-slate-400 md:text-[11px]">{data.header.statusDescription}</p>
            </div>
          </div>
        </header>

        <section className="mt-5">
          <p className="text-[10px] font-bold text-slate-500 md:text-xs">{data.header.title}</p>
          <h1 className="text-[18px] font-black tracking-tight text-slate-950 md:text-2xl">{data.header.subtitle}</h1>
        </section>

        <Card className="mt-4">
          <SectionTitle>{data.health.title}</SectionTitle>
          <div className="mt-3 flex items-center gap-5">
            <div className="relative grid h-24 w-24 shrink-0 place-items-center rounded-full" style={{ background: `conic-gradient(#10b981 ${data.health.score * 3.6}deg, #dff7ee 0deg)` }}>
              <div className="grid h-[68px] w-[68px] place-items-center rounded-full bg-white">
                <span className="text-xl font-black text-slate-950">{data.health.score}%</span>
              </div>
            </div>
            <ul className="min-w-0 space-y-2">
              {data.health.signals.map((signal) => (
                <li key={signal} className="text-[10px] font-bold text-slate-500 md:text-xs">{signal}</li>
              ))}
            </ul>
          </div>
        </Card>

        <Card className="mt-3">
          <SectionTitle>Accumulation</SectionTitle>
          <div className="mt-3 grid grid-cols-4 gap-2">
            {data.accumulation.map((metric) => (
              <div key={metric.id} className="text-center">
                <div className={`rounded-full px-2 py-1.5 text-[10px] font-black md:text-xs ${metricToneClass[metric.tone]}`}>{metric.value}</div>
                <p className="mt-1 text-[7px] font-extrabold text-slate-400 md:text-[10px]">{metric.label}</p>
              </div>
            ))}
          </div>
        </Card>

        <Card className="mt-3">
          <SectionTitle>Formation Pipeline</SectionTitle>
          <div className="mt-3 space-y-3">
            {data.pipeline.map((item) => (
              <div key={item.id} className="flex items-center gap-3">
                <span className={`h-5 w-5 rounded-full ${pipelineToneClass[item.tone]}`} />
                <span className="flex-1 text-[10px] font-bold text-slate-600 md:text-xs">{item.label}</span>
                <span className="text-[10px] font-extrabold text-slate-400 md:text-xs">{item.value}</span>
              </div>
            ))}
          </div>
        </Card>

        <Card className="mt-3">
          <SectionTitle>{data.gap.title}</SectionTitle>
          <p className="mt-2 text-[11px] font-extrabold leading-relaxed text-slate-700 md:text-sm">{data.gap.description}</p>
          <div className="mt-3 flex flex-wrap gap-2">
            {data.gap.tags.map((tag) => (
              <span key={tag.id} className={`rounded-full px-3 py-1.5 text-[9px] font-black md:text-[11px] ${gapToneClass[tag.tone]}`}>{tag.label}</span>
            ))}
          </div>
        </Card>

        <Card className="mt-3">
          <SectionTitle>Recent Knowledge</SectionTitle>
          <ul className="mt-2 space-y-1.5">
            {data.recentKnowledge.map((knowledge) => (
              <li key={knowledge} className="text-[11px] font-extrabold leading-relaxed text-slate-700 md:text-sm">・{knowledge}</li>
            ))}
          </ul>
        </Card>
      </div>
      <BottomNav active="knowledge" />
    </PhoneFrame>
  );
};
