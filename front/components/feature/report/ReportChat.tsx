"use client";

import { BottomNav } from "@/components/feature/discovery/BottomNav";
import { Card } from "@/components/ui/Card";
import { ChatBubble } from "@/components/ui/ChatBubble";
import { LoadingState } from "@/components/ui/LoadingState";
import { PhoneFrame } from "@/components/ui/PhoneFrame";
import { SectionTitle } from "@/components/ui/SectionTitle";
import { useReport } from "@/hooks/use-report";

export const ReportChat = () => {
  const { data, isLoading, isError } = useReport();

  if (isLoading) return <LoadingState message="Loading..." active="report" />;
  if (isError || !data) return <LoadingState message="情報の取得に失敗しました。" isError active="report" />;

  return (
    <PhoneFrame>
      <div className="px-5 pb-24 pt-5 md:px-7 md:pb-8 md:pt-8">
        <header className="flex items-center justify-between rounded-full bg-white px-3 py-2 shadow-[0_10px_24px_rgba(15,23,42,0.04)]">
          <div className="flex items-center gap-2">
            <div className="h-7 w-7 rounded-full bg-gradient-to-br from-amber-300 to-orange-500" />
            <div>
              <p className="text-[10px] font-extrabold text-amber-700 md:text-xs">{data.header.statusLabel}</p>
              <p className="text-[8px] font-semibold text-slate-400 md:text-[11px]">{data.header.statusDescription}</p>
            </div>
          </div>
        </header>

        <section className="mt-5">
          <h1 className="text-[20px] font-black tracking-tight text-slate-950 md:text-2xl">{data.header.title}</h1>
          <p className="mt-1 text-[11px] font-extrabold text-slate-500 md:text-sm">{data.header.subtitle}</p>
        </section>

        <div className="mt-4 rounded-full bg-orange-50 px-4 py-3 text-center text-[11px] font-black text-slate-600 shadow-[0_10px_24px_rgba(15,23,42,0.03)] md:text-sm">
          {data.topic}
        </div>

        <section className="mt-4 space-y-3">
          {data.messages.map((message) => (
            <ChatBubble key={message.id} message={message} />
          ))}
        </section>

        <Card className="mt-4">
          <SectionTitle>{data.extraction.title}</SectionTitle>
          <div className="mt-3 space-y-1.5">
            <p className="text-[10px] font-extrabold leading-relaxed text-slate-600 md:text-xs">
              <span className="text-slate-950">観測:</span> {data.extraction.observation}
            </p>
            <p className="text-[10px] font-extrabold leading-relaxed text-slate-600 md:text-xs">
              <span className="text-slate-950">関連する知識:</span> {data.extraction.entities}
            </p>
          </div>
        </Card>

        <button
          type="button"
          className="mt-4 flex w-full items-center gap-4 rounded-[28px] bg-gradient-to-r from-blue-500 to-teal-500 p-4 text-left text-white shadow-[0_18px_36px_rgba(14,165,233,0.22)] transition hover:-translate-y-0.5"
          aria-label={data.voiceAction.title}
        >
          <span className="grid h-14 w-14 shrink-0 place-items-center rounded-full bg-white/95 text-3xl font-black text-blue-500">↓</span>
          <span>
            <span className="block text-[16px] font-black leading-tight md:text-lg">{data.voiceAction.title}</span>
            <span className="mt-1 block text-[10px] font-extrabold text-white/90 md:text-xs">{data.voiceAction.description}</span>
          </span>
        </button>

        <label className="mt-5 block">
          <span className="sr-only">URL input</span>
          <input
            className="w-full rounded-full bg-white px-5 py-3 text-[10px] font-extrabold text-slate-500 outline-none shadow-[0_10px_24px_rgba(15,23,42,0.04)] placeholder:text-slate-400 md:text-xs"
            placeholder={data.urlPlaceholder}
            type="url"
          />
        </label>
      </div>
      <BottomNav active="report" />
    </PhoneFrame>
  );
};
