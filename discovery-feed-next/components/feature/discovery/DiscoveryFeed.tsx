"use client";

import { BottomNav } from "@/components/feature/discovery/BottomNav";
import { InsightCard } from "@/components/feature/discovery/InsightCard";
import { PhoneFrame } from "@/components/ui/PhoneFrame";
import { SectionTitle } from "@/components/ui/SectionTitle";
import { useDashboard } from "@/hooks/use-dashboard";

export const DiscoveryFeed = () => {
  const { data, isLoading, isError } = useDashboard();

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
        <header className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="h-7 w-7 rounded-full bg-gradient-to-br from-sky-400 to-blue-600" />
            <div>
              <p className="text-[10px] font-extrabold text-slate-600 md:text-xs">{data.consultant.name}</p>
              <p className="text-[8px] font-semibold text-slate-400 md:text-[11px]">{data.consultant.subtitle}</p>
            </div>
          </div>
          {data.consultant.isLive ? (
            <span className="rounded-full bg-blue-50 px-3 py-1 text-[8px] font-extrabold text-blue-600 ring-1 ring-blue-100 md:text-[10px]">LIVE</span>
          ) : null}
        </header>

        <section className="mt-6">
          <p className="text-[10px] font-bold text-slate-500 md:text-xs">Discovery Feed</p>
          <h1 className="text-[18px] font-black tracking-tight text-slate-950 md:text-2xl">コンサル発見を横断ダッシュボード</h1>
        </section>

        <section className="mt-4 rounded-[24px] bg-teal-900 p-5 text-white shadow-[0_18px_40px_rgba(15,118,110,0.22)] md:rounded-[28px]">
          <p className="text-sm font-extrabold md:text-base">{data.hero.title}</p>
          <p className="mt-1 text-4xl font-black leading-none md:text-5xl">{data.hero.count}</p>
          <p className="mt-3 text-[10px] font-bold text-teal-50/85 md:text-xs">{data.hero.summary}</p>
        </section>

        <section className="mt-4 space-y-3">
          {data.insights.map((insight) => (
            <InsightCard key={insight.id} insight={insight} />
          ))}
        </section>

        <section className="mt-6">
          <SectionTitle>Client Portfolio</SectionTitle>
          <div className="mt-3 grid grid-cols-3 gap-3 md:gap-4">
            {data.portfolio.map((client) => (
              <button
                key={client.id}
                className="rounded-2xl bg-white p-4 text-left shadow-[0_10px_24px_rgba(15,23,42,0.05)] transition hover:-translate-y-0.5 hover:shadow-[0_14px_34px_rgba(15,23,42,0.10)]"
                type="button"
              >
                <p className="text-[13px] font-black text-slate-950 md:text-sm">{client.name}</p>
                <p className="mt-1 text-[9px] font-bold text-slate-400 md:text-xs">{client.status}</p>
              </button>
            ))}
          </div>
        </section>

        <section className="mt-6">
          <SectionTitle>Next actions</SectionTitle>
          <div className="mt-3 space-y-3">
            {data.nextActions.map((action) => (
              <button
                key={action.id}
                className="w-full rounded-2xl bg-orange-50 p-4 text-left shadow-[0_10px_24px_rgba(15,23,42,0.04)] transition hover:-translate-y-0.5 hover:bg-orange-100"
                type="button"
              >
                <p className="text-[13px] font-black text-slate-950 md:text-sm">{action.title}</p>
                <p className="mt-1 text-[9px] font-bold text-slate-500 md:text-xs">{action.description}</p>
              </button>
            ))}
          </div>
        </section>
      </div>
      <BottomNav active="home" />
    </PhoneFrame>
  );
};
