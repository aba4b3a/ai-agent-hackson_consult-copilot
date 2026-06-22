"use client";

import { BottomNav } from "@/components/feature/discovery/BottomNav";
import { Card } from "@/components/ui/Card";
import { LoadingState } from "@/components/ui/LoadingState";
import { PhoneFrame } from "@/components/ui/PhoneFrame";
import { SectionTitle } from "@/components/ui/SectionTitle";
import { useReportCopilot } from "@/hooks/use-report-copilot";
import type { ReportCopilotHighlight } from "@/lib/schemas";

const toneStyles = {
  green: {
    badge: "bg-emerald-50 text-emerald-500",
    chip: "bg-emerald-50 text-emerald-500",
  },
  yellow: {
    badge: "bg-amber-50 text-amber-500",
    chip: "bg-amber-50 text-amber-500",
  },
};

const HighlightCard = ({ highlight }: { highlight: ReportCopilotHighlight }) => {
  const style = toneStyles[highlight.tone];

  return (
    <Card>
      <span className={`inline-flex rounded-full px-3 py-1 text-[8px] font-black md:text-[10px] ${style.badge}`}>{highlight.kind}</span>
      <h2 className="mt-3 text-[15px] font-black leading-tight text-slate-950 md:text-lg">{highlight.title}</h2>
      <p className="mt-1 text-[11px] font-extrabold leading-relaxed text-slate-600 md:text-sm">{highlight.description}</p>
      <p className={`mt-1 inline-flex rounded-full px-2.5 py-1 text-[8px] font-black md:text-[10px] ${style.chip}`}>{highlight.meta}</p>
    </Card>
  );
};

export const ReportCopilot = () => {
  const { data, isLoading, isError } = useReportCopilot();

  if (isLoading) return <LoadingState message="Loading..." />;
  if (isError || !data) return <LoadingState message="データの取得に失敗しました。" isError />;

  return (
    <PhoneFrame>
      <div className="px-5 pb-24 pt-6 md:px-7 md:pb-8 md:pt-9">
        <section>
          <h1 className="text-[20px] font-black leading-none tracking-tight text-slate-950 md:text-2xl">{data.header.title}</h1>
          <p className="mt-2 text-[11px] font-extrabold text-slate-500 md:text-sm">{data.header.subtitle}</p>
        </section>

        <section className="mt-5 rounded-[24px] bg-teal-900 p-5 text-white shadow-[0_18px_40px_rgba(15,118,110,0.22)] md:rounded-[28px]">
          <p className="text-[18px] font-black leading-tight md:text-2xl">{data.weekly.title}</p>
          <p className="mt-2 text-[11px] font-extrabold text-teal-50/90 md:text-sm">{data.weekly.period}</p>
          <p className="mt-3 text-[12px] font-black text-teal-50 md:text-sm">{data.weekly.summary}</p>
        </section>

        <section className="mt-4 space-y-3">
          {data.highlights.map((highlight) => (
            <HighlightCard key={highlight.id} highlight={highlight} />
          ))}
        </section>

        <Card className="mt-3">
          <SectionTitle>Evidence snippets</SectionTitle>
          <ul className="mt-3 space-y-1.5">
            {data.snippets.map((snippet) => (
              <li key={snippet} className="text-[11px] font-extrabold leading-relaxed text-slate-600 md:text-sm">
                - {snippet}
              </li>
            ))}
          </ul>
        </Card>

        <Card className="mt-3">
          <SectionTitle>{data.recommendation.title}</SectionTitle>
          <p className="mt-3 text-[11px] font-extrabold leading-relaxed text-slate-600 md:text-sm">{data.recommendation.description}</p>
          <button type="button" className="mt-3 rounded-full bg-blue-50 px-4 py-1.5 text-[9px] font-black text-blue-500 transition hover:bg-blue-100 md:text-[11px]">
            {data.recommendation.actionLabel}
          </button>
        </Card>

        <button
          type="button"
          className="mt-5 w-full rounded-[22px] bg-blue-600 px-6 py-4 text-[15px] font-black text-white shadow-[0_16px_32px_rgba(37,99,235,0.24)] transition hover:-translate-y-0.5 hover:bg-blue-700 md:text-base"
        >
          {data.ctaLabel}
        </button>
      </div>
      <BottomNav active="report" />
    </PhoneFrame>
  );
};
