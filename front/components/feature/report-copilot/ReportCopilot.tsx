"use client";

import { useState } from "react";
import { BottomNav } from "@/components/feature/discovery/BottomNav";
import { Card } from "@/components/ui/Card";
import { LoadingState } from "@/components/ui/LoadingState";
import { PhoneFrame } from "@/components/ui/PhoneFrame";
import { SectionTitle } from "@/components/ui/SectionTitle";
import { useReportCopilot } from "@/hooks/use-report-copilot";
import { sendCopilotMessage } from "@/services/report-copilot-service";
import type { MonthlyReportMetric, ReportCopilotHighlight, MonthlyReportSection } from "@/lib/schemas";
import { FiBarChart2, FiFileText, FiMessageCircle, FiRefreshCw } from "react-icons/fi";

type ChatEntry = { role: "user" | "assistant"; text: string };

const toneStyles = {
  green: { badge: "bg-emerald-50 text-emerald-700", bar: "bg-emerald-500", text: "text-emerald-700" },
  yellow: { badge: "bg-amber-50 text-amber-700", bar: "bg-amber-500", text: "text-amber-700" },
  blue: { badge: "bg-blue-50 text-blue-700", bar: "bg-blue-500", text: "text-blue-700" },
  slate: { badge: "bg-slate-100 text-slate-700", bar: "bg-slate-500", text: "text-slate-700" },
};

const HighlightCard = ({ highlight }: { highlight: ReportCopilotHighlight }) => (
  <article className="rounded-lg border border-slate-200 bg-white p-4">
    <span className={`inline-flex rounded-full px-3 py-1 text-[8px] font-black md:text-[10px] ${toneStyles[highlight.tone].badge}`}>
      {highlight.kind}
    </span>
    <h2 className="mt-3 text-[15px] font-black leading-tight text-slate-950 md:text-lg">{highlight.title}</h2>
    <p className="mt-1 text-[11px] font-extrabold leading-relaxed text-slate-600 md:text-sm">{highlight.description}</p>
    <p className={`mt-1 inline-flex rounded-full px-2.5 py-1 text-[8px] font-black md:text-[10px] ${toneStyles[highlight.tone].badge}`}>
      {highlight.meta}
    </p>
  </article>
);

const MetricTile = ({ metric }: { metric: MonthlyReportMetric }) => (
  <div className="rounded-lg border border-slate-200 bg-white p-3">
    <p className="text-[10px] font-black uppercase text-slate-500 md:text-xs">{metric.label}</p>
    <p className={`mt-2 text-xl font-black leading-none md:text-2xl ${toneStyles[metric.tone].text}`}>
      {metric.value}
      <span className="ml-1 text-[10px] text-slate-500 md:text-xs">{metric.unit}</span>
    </p>
  </div>
);

const BarChart = ({ items }: { items: MonthlyReportMetric[] }) => {
  const maxValue = Math.max(...items.map((item) => item.value), 1);

  return (
    <div className="space-y-3">
      {items.map((item) => (
        <div key={item.id} className="grid grid-cols-[4.5rem_1fr_3rem] items-center gap-2">
          <span className="text-[10px] font-black text-slate-600 md:text-xs">{item.label}</span>
          <div className="h-3 overflow-hidden rounded-full bg-slate-100">
            <div className={`h-full rounded-full ${toneStyles[item.tone].bar}`} style={{ width: `${Math.max(8, (item.value / maxValue) * 100)}%` }} />
          </div>
          <span className="text-right text-[10px] font-black text-slate-700 md:text-xs">
            {item.value}{item.unit}
          </span>
        </div>
      ))}
    </div>
  );
};

const ReportSection = ({ section }: { section: MonthlyReportSection }) => (
  <article className="border-t border-slate-200 py-4 first:border-t-0 first:pt-0 last:pb-0">
    <div className="flex items-center justify-between gap-3">
      <h2 className="text-sm font-black text-slate-950 md:text-base">{section.title}</h2>
      <span className={`shrink-0 rounded-full px-2.5 py-1 text-[8px] font-black uppercase md:text-[10px] ${
        section.kind === "hypothesis" ? toneStyles.yellow.badge : section.kind === "fact" ? toneStyles.green.badge : toneStyles.slate.badge
      }`}>
        {section.kind}
      </span>
    </div>
    <p className="mt-2 text-[11px] font-semibold leading-relaxed text-slate-700 md:text-sm">{section.body}</p>
  </article>
);

export const ReportCopilot = () => {
  const { data, isLoading, isError } = useReportCopilot();
  const [chat, setChat] = useState<ChatEntry[]>([]);
  const [input, setInput] = useState("");
  const [sessionId, setSessionId] = useState<string | undefined>();
  const [sending, setSending] = useState(false);

  const handleSend = async () => {
    const msg = input.trim();
    if (!msg || sending) return;
    setInput("");
    setChat((prev) => [...prev, { role: "user", text: msg }]);
    setSending(true);
    try {
      const res = await sendCopilotMessage(msg, sessionId);
      setSessionId(res.session_id);
      setChat((prev) => [...prev, { role: "assistant", text: res.reply }]);
    } catch {
      setChat((prev) => [...prev, { role: "assistant", text: "エラーが発生しました。再試行してください。" }]);
    } finally {
      setSending(false);
    }
  };

  if (isLoading) return <LoadingState message="Loading..." active="report" />;
  if (isError || !data) return <LoadingState message="月次レポートの取得に失敗しました。" isError active="report" />;

  return (
    <PhoneFrame>
      <div className="px-5 pb-24 pt-6 md:px-7 md:pb-8 md:pt-9">
        <section className="flex flex-col gap-3 border-b border-slate-200 pb-5 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="inline-flex items-center gap-1.5 rounded-full bg-white px-3 py-1 text-[10px] font-black text-slate-600 ring-1 ring-slate-200 md:text-xs">
              <FiFileText aria-hidden="true" className="h-3 w-3" />
              {data.monthly.source === "cloud_storage" ? "保存済み月次レポート" : "生成された月次レポート"}
            </p>
            <h1 className="mt-3 text-[22px] font-black leading-tight text-slate-950 md:text-3xl">{data.header.title}</h1>
            <p className="mt-2 text-[11px] font-extrabold text-slate-500 md:text-sm">{data.header.subtitle}</p>
          </div>
          <div className="text-left md:text-right">
            <p className="text-[10px] font-black uppercase text-slate-500 md:text-xs">{data.monthly.period}</p>
            <p className="mt-1 text-[10px] font-bold text-slate-400 md:text-xs">事実・仮説・根拠を分けて確認</p>
          </div>
        </section>

        <section className="mt-5 rounded-lg bg-slate-950 p-5 text-white">
          <div className="flex items-start gap-3">
            <FiFileText aria-hidden="true" className="mt-1 h-5 w-5 shrink-0 text-blue-200" />
            <div>
              <p className="text-[18px] font-black leading-tight md:text-2xl">{data.monthly.title}</p>
              <p className="mt-3 text-[12px] font-bold leading-relaxed text-slate-100 md:text-sm">{data.monthly.summary}</p>
            </div>
          </div>
        </section>

        <section className="mt-4 grid grid-cols-2 gap-2 md:grid-cols-4">
          {data.metrics.map((metric) => <MetricTile key={metric.id} metric={metric} />)}
        </section>

        <section className="mt-4 grid gap-4 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
          <Card className="rounded-lg">
            <div className="mb-4 flex items-center gap-2">
              <FiBarChart2 aria-hidden="true" className="h-4 w-4 text-blue-600" />
              <SectionTitle>月次の観測指標</SectionTitle>
            </div>
            <BarChart items={data.charts} />
          </Card>

          <Card className="rounded-lg">
            {data.sections.map((section) => <ReportSection key={section.id} section={section} />)}
          </Card>
        </section>

        <section className="mt-4 grid gap-3 lg:grid-cols-2">
          {data.highlights.map((h) => <HighlightCard key={h.id} highlight={h} />)}
        </section>

        <Card className="mt-4 rounded-lg">
          <SectionTitle>根拠となる観測メモ</SectionTitle>
          <ul className="mt-3 space-y-1.5">
            {data.snippets.map((s) => (
              <li key={s} className="text-[11px] font-extrabold leading-relaxed text-slate-600 md:text-sm">- {s}</li>
            ))}
          </ul>
        </Card>

        {/* チャットエリア */}
        <Card className="mt-4 rounded-lg">
          <div className="flex items-center gap-2">
            <FiMessageCircle aria-hidden="true" className="h-4 w-4 text-blue-600" />
            <SectionTitle>レポートを深掘りする</SectionTitle>
          </div>
          {chat.length > 0 && (
            <div className="mt-3 space-y-2 max-h-56 overflow-y-auto">
              {chat.map((entry, i) => (
                <div
                  key={i}
                  className={`rounded-2xl px-3 py-2 text-[11px] font-extrabold md:text-sm ${
                    entry.role === "user"
                      ? "ml-6 bg-blue-50 text-blue-900"
                      : "mr-6 bg-slate-100 text-slate-800"
                  }`}
                >
                  {entry.text}
                </div>
              ))}
              {sending && (
                <div className="mr-6 rounded-2xl bg-slate-100 px-3 py-2 text-[11px] font-extrabold text-slate-400 md:text-sm">
                  考え中...
                </div>
              )}
            </div>
          )}
          <div className="mt-3 flex gap-2">
            <input
              className="flex-1 rounded-full bg-slate-50 px-4 py-2.5 text-[11px] font-extrabold text-slate-800 outline-none ring-1 ring-slate-200 placeholder:text-slate-400 md:text-sm"
              placeholder="例: 次回訪問で何を確認すべき？"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSend()}
              disabled={sending}
            />
            <button
              type="button"
              onClick={handleSend}
              disabled={sending || !input.trim()}
              className="inline-flex shrink-0 items-center gap-1.5 rounded-full bg-blue-600 px-4 py-2.5 text-[11px] font-black text-white disabled:opacity-40 md:text-sm"
            >
              <FiRefreshCw aria-hidden="true" className="h-3 w-3" />
              送信
            </button>
          </div>
        </Card>
      </div>
      <BottomNav active="report" />
    </PhoneFrame>
  );
};
