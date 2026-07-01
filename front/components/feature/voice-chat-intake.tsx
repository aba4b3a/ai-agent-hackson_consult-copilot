"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { Send } from "lucide-react";

import { useFollowups } from "@/hooks/use-followups";
import { useSubmitVoice } from "@/hooks/use-submit-voice";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { ChatBubble } from "@/components/ui/chat-bubble";
import { Input } from "@/components/ui/field";

/**
 * Conversational (text) field intake (§5, text-only for M2). The assistant
 * asks a fixed opener, then follow-up questions are generated dynamically from
 * the user's answer + the workspace observation policy (R12.4) via the agent
 * (Gemini when configured, mock otherwise). Bounded turns; skippable (R12.8).
 * Real Speech-to-Text/Text-to-Speech is a later milestone.
 */
const OPENER = "今日、顧客から普段と違う反応や相談はありましたか。";
const MAX_TURNS = 5;

type Turn = { question: string; answer: string };

export function VoiceChatIntake({ workspaceId }: { workspaceId: string }) {
  const router = useRouter();
  const [turns, setTurns] = useState<Turn[]>([]);
  const [pending, setPending] = useState<string | null>(OPENER);
  // Only the setter is used; the queue is read via the functional updater.
  const [, setQueue] = useState<string[]>([]);
  const [fetched, setFetched] = useState(false);
  const [draft, setDraft] = useState("");

  const followups = useFollowups(workspaceId);
  const submit = useSubmitVoice();

  const finished = pending === null && !followups.isPending;
  const transcript = useMemo(
    () => turns.map((t) => `Q: ${t.question}\nA: ${t.answer}`).join("\n"),
    [turns],
  );

  function advanceFromQueue() {
    setQueue((prev) => {
      const [next, ...rest] = prev;
      setPending(next ?? null);
      return rest;
    });
  }

  function handleSend() {
    if (!draft.trim() || pending === null) return;
    const answer = draft.trim();
    const nextTurns = [...turns, { question: pending, answer }];
    setTurns(nextTurns);
    setDraft("");

    if (nextTurns.length >= MAX_TURNS) {
      setPending(null);
      return;
    }

    if (!fetched) {
      // First answer: fetch dynamic follow-ups based on it + observation policy.
      setPending(null);
      followups.mutate(
        nextTurns.map((t) => t.answer),
        {
          onSuccess: (questions) => {
            setFetched(true);
            const [first, ...rest] = questions;
            setQueue(rest);
            setPending(first ?? null);
          },
          onError: () => setFetched(true),
        },
      );
      return;
    }

    advanceFromQueue();
  }

  function handleSkip() {
    setQueue([]);
    setPending(null);
  }

  return (
    <Card>
      <div className="space-y-3">
        {turns.map((turn, index) => (
          <div key={index} className="space-y-3">
            <ChatBubble role="assistant">{turn.question}</ChatBubble>
            <ChatBubble role="user">{turn.answer}</ChatBubble>
          </div>
        ))}
        {followups.isPending ? (
          <ChatBubble role="assistant">少し考えています…</ChatBubble>
        ) : null}
        {pending ? <ChatBubble role="assistant">{pending}</ChatBubble> : null}
      </div>

      {!finished ? (
        <div className="mt-4 space-y-2">
          <div className="flex items-center gap-2">
            <Input
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleSend();
              }}
              placeholder="話すように入力してください"
              disabled={followups.isPending || pending === null}
            />
            <Button
              size="icon"
              aria-label="Send"
              disabled={!draft.trim() || followups.isPending || pending === null}
              onClick={handleSend}
            >
              <Send size={16} />
            </Button>
          </div>
          {turns.length > 0 && !followups.isPending ? (
            <button
              type="button"
              onClick={handleSkip}
              className="text-xs text-text-muted underline"
            >
              質問をスキップして送信内容を確認
            </button>
          ) : null}
        </div>
      ) : (
        <div className="mt-4 space-y-3">
          <div className="rounded-md border border-border bg-background p-3">
            <p className="text-xs font-medium uppercase tracking-[0.12em] text-text-muted">送信内容の確認</p>
            <pre className="mt-2 whitespace-pre-wrap text-sm leading-6 text-text">{transcript}</pre>
          </div>
          {submit.isError ? (
            <p className="text-sm text-danger">送信に失敗しました。時間をおいて再試行してください。</p>
          ) : null}
          <Button
            className="w-full"
            disabled={submit.isPending || !workspaceId || turns.length === 0}
            onClick={() =>
              submit.mutate(
                { workspace_id: workspaceId, transcript, submitted_by_role: "field_staff" },
                { onSuccess: () => router.push("/") },
              )
            }
          >
            {submit.isPending ? "送信中…" : "この内容で送信"}
          </Button>
        </div>
      )}
    </Card>
  );
}
