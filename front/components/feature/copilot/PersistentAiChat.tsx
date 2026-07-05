"use client";

import { FormEvent, useMemo, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@/components/feature/auth/AuthProvider";
import { getKnowledgeData } from "@/services/knowledge-service";
import { sendCopilotMessage } from "@/services/report-copilot-service";
import { listWikiFiles, readWikiFile } from "@/services/wiki-service";

type ChatEntry = {
  role: "user" | "assistant";
  text: string;
};

const starterPrompts = [
  "今の重点管理指標で優先して見るべき変化は？",
  "この企業のKPI候補と根拠を整理して",
  "次にResearch Agentが聞くべき質問は？",
];

const buildGroundedPrompt = ({
  question,
  companyCode,
  wikiPaths,
  wikiSnippets,
  knowledgeSignals,
}: {
  question: string;
  companyCode: string;
  wikiPaths: string[];
  wikiSnippets: string[];
  knowledgeSignals: string[];
}) => {
  const wikiContext = wikiPaths.length > 0 ? wikiPaths.join(", ") : "current LLM Wiki files";
  const wikiEvidence = wikiSnippets.length > 0 ? wikiSnippets.join("\n---\n") : "No Wiki snippet could be loaded before this request.";
  const signalContext = knowledgeSignals.length > 0 ? knowledgeSignals.join(" / ") : "BigQuery knowledge stats and current definitions";

  return [
    "Consult Copilot persistent chat request.",
    `company_id: ${companyCode}`,
    "回答時は、可能な限り LLM Wiki と BigQuery の構造化データを参照し、根拠があるものと仮説を分けてください。",
    `LLM Wiki candidates: ${wikiContext}`,
    `LLM Wiki snippets:\n${wikiEvidence}`,
    `BigQuery context candidates: ${signalContext}`,
    `User question: ${question}`,
  ].join("\n");
};

export const PersistentAiChat = () => {
  const { activeCompany, session } = useAuth();
  const [messages, setMessages] = useState<ChatEntry[]>([
    {
      role: "assistant",
      text: "LLM Wiki と BigQuery の情報を前提に、KPI候補、重点管理指標、観測方針、追加質問を一緒に確認できます。",
    },
  ]);
  const [input, setInput] = useState("");
  const [sessionId, setSessionId] = useState<string | undefined>();
  const [sending, setSending] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const wikiContext = useQuery({
    queryKey: ["persistent-chat-wiki-context", activeCompany.code],
    queryFn: async () => {
      const files = await listWikiFiles(activeCompany.code);
      const readableFiles = files.items
        .map((item) => item.path)
        .filter((path) => path.endsWith(".md") || path.endsWith(".yaml") || path.endsWith(".json"))
        .slice(0, 3);

      const contents = await Promise.allSettled(
        readableFiles.map((path) => readWikiFile(path, undefined, activeCompany.code)),
      );

      return {
        files,
        snippets: contents.flatMap((result) => {
          if (result.status !== "fulfilled") return [];
          const compactContent = result.value.content.replace(/\s+/g, " ").trim();
          return [`${result.value.path}: ${compactContent.slice(0, 700)}`];
        }),
      };
    },
    enabled: Boolean(session),
    staleTime: 30_000,
    retry: 1,
  });

  const knowledge = useQuery({
    queryKey: ["persistent-chat-knowledge", activeCompany.code],
    queryFn: () => getKnowledgeData(activeCompany.code),
    enabled: Boolean(session),
    staleTime: 30_000,
    retry: 1,
  });

  const wikiPaths = useMemo(() => {
    return (wikiContext.data?.files.items ?? []).slice(0, 5).map((item) => item.path);
  }, [wikiContext.data?.files.items]);

  const wikiSnippets = useMemo(() => {
    return wikiContext.data?.snippets ?? [];
  }, [wikiContext.data?.snippets]);

  const knowledgeSignals = useMemo(() => {
    const data = knowledge.data;
    if (!data) return [];

    return [
      data.header.statusLabel,
      ...data.health.signals.slice(0, 2),
      ...data.recentKnowledge.slice(0, 2),
    ].filter(Boolean);
  }, [knowledge.data]);

  const sourceStatus = [
    { label: "企業情報", ready: wikiContext.isSuccess, loading: wikiContext.isLoading },
    { label: "各種データ", ready: knowledge.isSuccess, loading: knowledge.isLoading },
    { label: "AI", ready: true, loading: false },
  ];

  const ask = async (question: string) => {
    const trimmed = question.trim();
    if (!trimmed || sending) return;

    setInput("");
    setMessages((prev) => [...prev, { role: "user", text: trimmed }]);
    setSending(true);

    try {
      const groundedPrompt = buildGroundedPrompt({
        question: trimmed,
        companyCode: activeCompany.code,
        wikiPaths,
        wikiSnippets,
        knowledgeSignals,
      });
      const response = await sendCopilotMessage(groundedPrompt, sessionId, activeCompany.code);
      setSessionId(response.session_id);
      setMessages((prev) => [...prev, { role: "assistant", text: response.reply }]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: "Copilot APIに接続できませんでした。バックエンドとAgent Runtimeが起動しているか確認してください。",
        },
      ]);
    } finally {
      setSending(false);
    }
  };

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    void ask(input);
  };

  return (
    <aside className="fixed inset-y-0 right-0 z-30 hidden w-[26rem] border-l border-slate-200 bg-white text-slate-950 shadow-[-18px_0_40px_rgba(15,23,42,0.08)] xl:flex xl:flex-col">
      <header className="border-b border-slate-100 px-5 pb-4 pt-5">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-[10px] font-black uppercase tracking-normal text-blue-600">AI Chat</p>
            <h2 className="mt-1 text-lg font-black">Consult Copilot</h2>
            <p className="mt-1 text-xs font-bold leading-5 text-slate-500">{activeCompany.code} / {activeCompany.name}</p>
          </div>
          <span className="rounded-md bg-emerald-50 px-2.5 py-1 text-[10px] font-black text-emerald-700">PC</span>
        </div>

        <div className="mt-4 grid grid-cols-3 gap-2">
          {sourceStatus.map((source) => (
            <div key={source.label} className="rounded-md border border-slate-200 px-2 py-2">
              <p className="text-[10px] font-black text-slate-600">{source.label}</p>
              <p className={`mt-1 text-[10px] font-black ${source.ready ? "text-emerald-600" : source.loading ? "text-amber-600" : "text-slate-400"}`}>
                {source.ready ? "参照可" : source.loading ? "読込中" : "未接続"}
              </p>
            </div>
          ))}
        </div>
      </header>

      <div className="flex-1 overflow-y-auto px-5 py-4">
        <div className="space-y-3">
          {messages.map((message, index) => (
            <div
              key={`${message.role}-${index}`}
              className={`rounded-lg px-3 py-2.5 text-sm font-semibold leading-6 ${
                message.role === "user"
                  ? "ml-8 bg-blue-600 text-white"
                  : "mr-8 border border-slate-200 bg-slate-50 text-slate-800"
              }`}
            >
              {message.text}
            </div>
          ))}
          {sending ? (
            <div className="mr-8 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm font-bold text-slate-500">
              Wiki と BigQuery の文脈を確認しています...
            </div>
          ) : null}
        </div>
      </div>

      <div className="border-t border-slate-100 px-5 py-4">
        <div className="mb-3 flex gap-2 overflow-x-auto pb-1">
          {starterPrompts.map((prompt) => (
            <button
              key={prompt}
              type="button"
              className="shrink-0 rounded-md border border-slate-200 bg-white px-3 py-2 text-left text-[11px] font-bold text-slate-600 transition hover:border-blue-200 hover:bg-blue-50 hover:text-blue-700"
              onClick={() => {
                setInput(prompt);
                inputRef.current?.focus();
              }}
            >
              {prompt}
            </button>
          ))}
        </div>

        <form className="flex gap-2" onSubmit={handleSubmit}>
          <input
            ref={inputRef}
            className="min-w-0 flex-1 rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-sm font-semibold outline-none transition placeholder:text-slate-400 focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
            placeholder="KPI、重点指標、観測方針について質問"
            value={input}
            onChange={(event) => setInput(event.target.value)}
            disabled={sending}
          />
          <button
            type="submit"
            className="rounded-lg bg-slate-950 px-4 py-2.5 text-sm font-black text-white transition hover:bg-slate-800 disabled:opacity-40"
            disabled={sending || !input.trim()}
          >
            送信
          </button>
        </form>
      </div>
    </aside>
  );
};
