"use client";

import { FormEvent, PointerEvent as ReactPointerEvent, useEffect, useMemo, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { FiMessageCircle, FiX } from "react-icons/fi";
import { useAuth } from "@/components/feature/auth/AuthProvider";
import { ChatMarkdown } from "@/components/ui/ChatMarkdown";
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

// デスクトップ(xl以上)のパネル幅。CSS変数 --copilot-w を通じて PhoneFrame の
// 本文余白と連動させる（ドラッグ中はReactを再レンダリングせずCSS変数だけ更新
// することで、全画面分の本文をスムーズに追従させる）。
const DEFAULT_PANEL_WIDTH_PX = 416; // 26rem = 従来の固定幅
const MIN_PANEL_WIDTH_PX = 320;
const PANEL_WIDTH_STORAGE_KEY = "knowledge-farmer.copilot-width";

const clampPanelWidth = (width: number) =>
  Math.min(Math.max(width, MIN_PANEL_WIDTH_PX), Math.min(640, Math.floor(window.innerWidth * 0.5)));

const applyPanelWidthVar = (width: number) => {
  document.documentElement.style.setProperty("--copilot-w", `${width}px`);
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

  // ---- xl未満: フローティングボタン＋ボトムシートの開閉 ----
  const [isMobileOpen, setIsMobileOpen] = useState(false);

  useEffect(() => {
    if (!isMobileOpen) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = previousOverflow;
    };
  }, [isMobileOpen]);

  // ---- xl以上: 左端ドラッグによるパネル幅の変更 ----
  const panelWidthRef = useRef(DEFAULT_PANEL_WIDTH_PX);
  const isResizingRef = useRef(false);

  useEffect(() => {
    // localStorage はクライアントでのみ読める。静的エクスポートのため
    // マウント後に復元する（NavVisibilityProvider と同じ流儀）。
    const stored = Number(window.localStorage.getItem(PANEL_WIDTH_STORAGE_KEY));
    if (Number.isFinite(stored) && stored > 0) {
      const width = clampPanelWidth(stored);
      panelWidthRef.current = width;
      applyPanelWidthVar(width);
    }
  }, []);

  const startResize = (event: ReactPointerEvent<HTMLDivElement>) => {
    event.preventDefault();
    event.currentTarget.setPointerCapture(event.pointerId);
    isResizingRef.current = true;
    document.body.style.userSelect = "none";
    document.body.style.cursor = "col-resize";
  };

  const moveResize = (event: ReactPointerEvent<HTMLDivElement>) => {
    if (!isResizingRef.current) return;
    const width = clampPanelWidth(window.innerWidth - event.clientX);
    panelWidthRef.current = width;
    applyPanelWidthVar(width);
  };

  const endResize = () => {
    if (!isResizingRef.current) return;
    isResizingRef.current = false;
    document.body.style.userSelect = "";
    document.body.style.cursor = "";
    window.localStorage.setItem(PANEL_WIDTH_STORAGE_KEY, String(panelWidthRef.current));
  };

  const resetPanelWidth = () => {
    panelWidthRef.current = DEFAULT_PANEL_WIDTH_PX;
    applyPanelWidthVar(DEFAULT_PANEL_WIDTH_PX);
    window.localStorage.setItem(PANEL_WIDTH_STORAGE_KEY, String(DEFAULT_PANEL_WIDTH_PX));
  };

  // デスクトップの右固定パネルとモバイルのボトムシートで同じ中身を使う。
  // state はコンポーネント直下で共有しているため、画面幅が変わっても会話は継続する。
  const renderPanelBody = (onClose?: () => void) => (
    <>
      <header className="border-b border-slate-100 px-5 pb-4 pt-5">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-[10px] font-black uppercase tracking-normal text-blue-600">Report Copilot</p>
            <h2 className="mt-1 text-lg font-black">Knowledge Farmer</h2>
            <p className="mt-1 text-xs font-bold leading-5 text-slate-500">{activeCompany.code} / {activeCompany.name}</p>
          </div>
          {onClose ? (
            <button
              type="button"
              onClick={onClose}
              aria-label="チャットを閉じる"
              className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-slate-100 text-slate-600 transition hover:bg-slate-200"
            >
              <FiX aria-hidden="true" className="h-4 w-4" />
            </button>
          ) : (
            <span className="rounded-md bg-emerald-50 px-2.5 py-1 text-[10px] font-black text-emerald-700">PC</span>
          )}
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
                  ? "ml-8 whitespace-pre-line bg-blue-600 text-white"
                  : "mr-8 border border-slate-200 bg-slate-50 text-slate-800"
              }`}
            >
              {message.role === "assistant" ? <ChatMarkdown text={message.text} /> : message.text}
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
    </>
  );

  return (
    <>
      {/* xl以上: 右固定パネル（左端ドラッグで幅変更、ダブルクリックでリセット） */}
      <aside className="fixed inset-y-0 right-0 z-30 hidden w-[var(--copilot-w,26rem)] border-l border-slate-200 bg-white text-slate-950 shadow-[-18px_0_40px_rgba(15,23,42,0.08)] xl:flex xl:flex-col">
        <div
          role="separator"
          aria-orientation="vertical"
          aria-label="チャットパネルの幅を変更"
          title="ドラッグで幅を変更 / ダブルクリックでリセット"
          className="absolute inset-y-0 left-0 z-10 w-1.5 cursor-col-resize bg-transparent transition hover:bg-blue-300 active:bg-blue-400"
          onPointerDown={startResize}
          onPointerMove={moveResize}
          onPointerUp={endResize}
          onPointerCancel={endResize}
          onDoubleClick={resetPanelWidth}
        />
        {renderPanelBody()}
      </aside>

      {/* xl未満: フローティングボタン */}
      {!isMobileOpen ? (
        <button
          type="button"
          onClick={() => setIsMobileOpen(true)}
          aria-label="AIチャットを開く"
          className="fixed bottom-20 right-4 z-40 inline-flex items-center gap-2 rounded-full bg-slate-950 px-4 py-3 text-sm font-black text-white shadow-[0_14px_30px_rgba(15,23,42,0.35)] transition hover:bg-slate-800 md:bottom-6 xl:hidden"
        >
          <FiMessageCircle aria-hidden="true" className="h-5 w-5" />
          AI
        </button>
      ) : null}

      {/* xl未満: ボトムシート（サイドナビの開閉トグル(z-40)より上に重ねる） */}
      {isMobileOpen ? (
        <div className="fixed inset-0 z-50 xl:hidden">
          <div
            className="absolute inset-0 bg-slate-950/40"
            onClick={() => setIsMobileOpen(false)}
            aria-hidden="true"
          />
          <div
            role="dialog"
            aria-modal="true"
            aria-label="Report Copilot チャット"
            className="absolute inset-x-0 bottom-0 flex h-[85dvh] flex-col rounded-t-2xl bg-white text-slate-950 shadow-[0_-18px_40px_rgba(15,23,42,0.2)]"
          >
            {renderPanelBody(() => setIsMobileOpen(false))}
          </div>
        </div>
      ) : null}
    </>
  );
};
