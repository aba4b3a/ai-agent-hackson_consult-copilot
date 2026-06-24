"use client";

import { useState } from "react";
import { BottomNav } from "@/components/feature/discovery/BottomNav";
import { Card } from "@/components/ui/Card";
import { LoadingState } from "@/components/ui/LoadingState";
import { PhoneFrame } from "@/components/ui/PhoneFrame";
import { SectionTitle } from "@/components/ui/SectionTitle";
import { useReportCopilot } from "@/hooks/use-report-copilot";
import { sendCopilotMessage } from "@/services/report-copilot-service";
import type { ReportCopilotHighlight } from "@/lib/schemas";

type ChatEntry = { role: "user" | "assistant"; text: string };

const toneStyles = {
  green: { badge: "bg-emerald-50 text-emerald-500" },
  yellow: { badge: "bg-amber-50 text-amber-500" },
};

const HighlightCard = ({ highlight }: { highlight: ReportCopilotHighlight }) => (
  <Card>
    <span className={`inline-flex rounded-full px-3 py-1 text-[8px] font-black md:text-[10px] ${toneStyles[highlight.tone].badge}`}>
      {highlight.kind}
    </span>
    <h2 className="mt-3 text-[15px] font-black leading-tight text-slate-950 md:text-lg">{highlight.title}</h2>
    <p className="mt-1 text-[11px] font-extrabold leading-relaxed text-slate-600 md:text-sm">{highlight.description}</p>
    <p className={`mt-1 inline-flex rounded-full px-2.5 py-1 text-[8px] font-black md:text-[10px] ${toneStyles[highlight.tone].badge}`}>
      {highlight.meta}
    </p>
  </Card>
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

  if (isLoading) return <LoadingState message="Loading..." />;
  if (isError || !data) return <LoadingState message="データの取得に失敗しました。" isError />;

  return (
    <PhoneFrame>
      <div className="px-5 pb-24 pt-6 md:px-7 md:pb-8 md:pt-9">
        <section>
          <h1 className="text-[20px] font-black leading-none tracking-tight text-slate-950 md:text-2xl">{data.header.title}</h1>
          <p className="mt-2 text-[11px] font-extrabold text-slate-500 md:text-sm">{data.header.subtitle}</p>
        </section>

        <section className="mt-5 rounded-[24px] bg-teal-900 p-5 text-white shadow-[0_18px_40px_rgba(15,118,110,0.22)]">
          <p className="text-[18px] font-black leading-tight md:text-2xl">{data.weekly.title}</p>
          <p className="mt-2 text-[11px] font-extrabold text-teal-50/90 md:text-sm">{data.weekly.period}</p>
          <p className="mt-3 text-[12px] font-black text-teal-50 md:text-sm">{data.weekly.summary}</p>
        </section>

        <section className="mt-4 space-y-3">
          {data.highlights.map((h) => <HighlightCard key={h.id} highlight={h} />)}
        </section>

        <Card className="mt-3">
          <SectionTitle>Evidence snippets</SectionTitle>
          <ul className="mt-3 space-y-1.5">
            {data.snippets.map((s) => (
              <li key={s} className="text-[11px] font-extrabold leading-relaxed text-slate-600 md:text-sm">- {s}</li>
            ))}
          </ul>
        </Card>

        {/* チャットエリア */}
        <Card className="mt-4">
          <SectionTitle>Copilot に質問する</SectionTitle>
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
              placeholder="例: 価格不満の原因は？"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSend()}
              disabled={sending}
            />
            <button
              type="button"
              onClick={handleSend}
              disabled={sending || !input.trim()}
              className="shrink-0 rounded-full bg-blue-600 px-4 py-2.5 text-[11px] font-black text-white disabled:opacity-40 md:text-sm"
            >
              送信
            </button>
          </div>
        </Card>
      </div>
      <BottomNav active="report" />
    </PhoneFrame>
  );
};
