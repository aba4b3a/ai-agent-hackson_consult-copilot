import type { DiscoveryInsight } from "@/lib/schemas";

const priorityStyles = {
  danger: {
    bg: "bg-rose-100",
    text: "text-rose-500",
    icon: "▲",
  },
  success: {
    bg: "bg-emerald-100",
    text: "text-emerald-500",
    icon: "●",
  },
  neutral: {
    bg: "bg-slate-100",
    text: "text-slate-500",
    icon: "●",
  },
};

export const InsightCard = ({ insight }: { insight: DiscoveryInsight }) => {
  const style = priorityStyles[insight.priority];

  return (
    <article className="flex gap-3 rounded-2xl bg-white p-3 shadow-[0_10px_24px_rgba(15,23,42,0.06)] transition hover:-translate-y-0.5 hover:shadow-[0_14px_34px_rgba(15,23,42,0.10)]">
      <div className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-xl ${style.bg} ${style.text}`}>
        <span className="text-lg leading-none">{style.icon}</span>
      </div>
      <div className="min-w-0">
        <h3 className="text-[13px] font-extrabold leading-tight text-slate-950 md:text-sm">{insight.title}</h3>
        <p className="mt-1 text-[10px] font-semibold text-slate-500 md:text-xs">{insight.description}</p>
        <p className="mt-1 truncate text-[8px] font-semibold text-slate-400 md:text-[11px]">{insight.meta}</p>
      </div>
    </article>
  );
};
