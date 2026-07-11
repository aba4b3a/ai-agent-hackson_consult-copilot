"use client";

import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@/components/feature/auth/AuthProvider";
import { getKnowledgeData } from "@/services/knowledge-service";
import { sendCopilotMessage } from "@/services/report-copilot-service";
import { listWikiFiles, readWikiFile, toRelativeWikiPath } from "@/services/wiki-service";

type ChatEntry = {
  role: "user" | "assistant";
  text: string;
};

type StoredChat = {
  messages: ChatEntry[];
  sessionId?: string;
};

const defaultGreeting: ChatEntry = {
  role: "assistant",
  text: "企業のナレッジと直近の観測を前提に、次回ヒアリング、変化の兆候、追加で確認すべきことを一緒に整理できます。",
};

const chatStorageKey = (companyCode: string) => `knowledge-farmer.persistent-chat.${companyCode}`;

const loadStoredChat = (companyCode: string): StoredChat | null => {
  if (typeof window === "undefined") return null;
  const raw = window.localStorage.getItem(chatStorageKey(companyCode));
  if (!raw) return null;
  try {
    return JSON.parse(raw) as StoredChat;
  } catch {
    return null;
  }
};

const saveStoredChat = (companyCode: string, state: StoredChat) => {
  window.localStorage.setItem(chatStorageKey(companyCode), JSON.stringify(state));
};

const starterPrompts = [
  "次回訪問で何を確認すべき？",
  "今月の変化の兆候と根拠を整理して",
  "次に現場へ聞くべき質問は？",
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
  const wikiContext = wikiPaths.length > 0 ? wikiPaths.join(", ") : "current company knowledge files";
  const wikiEvidence = wikiSnippets.length > 0 ? wikiSnippets.join("\n---\n") : "No company knowledge snippet could be loaded before this request.";
  const signalContext = knowledgeSignals.length > 0 ? knowledgeSignals.join(" / ") : "current knowledge signals and observation themes";

  return [
    "Knowledge Farmer persistent chat request.",
    `company_id: ${companyCode}`,
    "回答方針:",
    "- 挨拶や雑談など、具体的な質問を含まない発言には、参考情報を無理に使わず、短く自然な会話として応答してください。",
    "- 企業課題、顧客の声、観測テーマ、仮説、次回ヒアリングに関する質問には、可能な限り下記の企業ナレッジと観測情報を参照し、事実と仮説を分けて回答してください。",
    `Company knowledge candidates: ${wikiContext}`,
    `Company knowledge snippets:\n${wikiEvidence}`,
    `Observation context candidates: ${signalContext}`,
    `User question: ${question}`,
  ].join("\n");
};

export const PersistentAiChat = () => {
  const { activeCompany, session } = useAuth();
  const [messages, setMessages] = useState<ChatEntry[]>(() => {
    const stored = loadStoredChat(activeCompany.code);
    return stored?.messages?.length ? stored.messages : [defaultGreeting];
  });
  const [input, setInput] = useState("");
  const [sessionId, setSessionId] = useState<string | undefined>(
    () => loadStoredChat(activeCompany.code)?.sessionId,
  );
  const [sending, setSending] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const activeCompanyCodeRef = useRef(activeCompany.code);
  const isFirstCompanyRender = useRef(true);

  // 企業を切り替えたら、その企業の保存済み会話に差し替える（保存は下のeffectで現在の企業コードに書き込む）。
  useEffect(() => {
    activeCompanyCodeRef.current = activeCompany.code;
    if (isFirstCompanyRender.current) {
      isFirstCompanyRender.current = false;
      return;
    }
    const stored = loadStoredChat(activeCompany.code);
    setMessages(stored?.messages?.length ? stored.messages : [defaultGreeting]);
    setSessionId(stored?.sessionId);
  }, [activeCompany.code]);

  useEffect(() => {
    saveStoredChat(activeCompanyCodeRef.current, { messages, sessionId });
  }, [messages, sessionId]);

  const wikiContext = useQuery({
    queryKey: ["persistent-chat-wiki-context", activeCompany.code],
    queryFn: async () => {
      const files = await listWikiFiles(activeCompany.code);
      const readableFiles = files.items
        .map((item) => item.path)
        .filter((path) => path.endsWith(".md") || path.endsWith(".yaml") || path.endsWith(".json"))
        .slice(0, 3);

      const contents = await Promise.allSettled(
        readableFiles.map((path) => readWikiFile(toRelativeWikiPath(path), undefined, activeCompany.code)),
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
    { label: "企業ナレッジ", ready: wikiContext.isSuccess, loading: wikiContext.isLoading },
    { label: "観測メモ", ready: knowledge.isSuccess, loading: knowledge.isLoading },
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
          text: "一時的に回答を生成できませんでした。少し時間をおいて再度お試しください。",
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
            <p className="text-[10px] font-black uppercase tracking-normal text-blue-600">Report Copilot</p>
            <h2 className="mt-1 text-lg font-black">Knowledge Farmer</h2>
            <p className="mt-1 text-xs font-bold leading-5 text-slate-500">{activeCompany.code} / {activeCompany.name}</p>
          </div>
          <span className="rounded-md bg-emerald-50 px-2.5 py-1 text-[10px] font-black text-emerald-700">PC</span>
        </div>

        <div className="mt-4 grid grid-cols-3 gap-2">
          {sourceStatus.map((source) => (
            <div key={source.label} className="rounded-md border border-slate-200 px-2 py-2">
              <p className="text-[10px] font-black text-slate-600">{source.label}</p>
              <p className={`mt-1 text-[10px] font-black ${source.ready ? "text-emerald-600" : source.loading ? "text-amber-600" : "text-slate-400"}`}>
                {source.ready ? "参照可" : source.loading ? "読込中" : "未取得"}
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
              企業ナレッジと観測メモを確認しています...
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
            placeholder="次回ヒアリングや変化の兆候について質問"
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
