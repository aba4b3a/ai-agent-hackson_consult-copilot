"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { Send } from "lucide-react";

import { useSubmitVoice } from "@/hooks/use-submit-voice";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { ChatBubble } from "@/components/ui/chat-bubble";
import { Input } from "@/components/ui/field";

/**
 * Conversational (text) field intake (§5, text-only for M2). The assistant asks
 * a bounded sequence of follow-up questions (§5.4), then the collected answers
 * are assembled into a transcript and submitted as a voice_transcript source.
 * Real Speech-to-Text/Text-to-Speech is a later milestone.
 */
const PROMPTS = [
  "今日、顧客から普段と違う反応や相談はありましたか。",
  "それは普段と比べてどう違いましたか。原因に心当たりはありますか。",
  "どの顧客層・商品・競合名と関係していましたか。",
  "売上や再来店などの業務への影響につながりそうですか。",
];
const MAX_TURNS = PROMPTS.length;

type Turn = { question: string; answer: string };

export function VoiceChatIntake({ workspaceId }: { workspaceId: string }) {
  const router = useRouter();
  const [turns, setTurns] = useState<Turn[]>([]);
  const [draft, setDraft] = useState("");
  const submit = useSubmitVoice();

  const currentPrompt = turns.length < MAX_TURNS ? PROMPTS[turns.length] : null;
  const finished = currentPrompt === null;

  const transcript = useMemo(
    () => turns.map((t) => `Q: ${t.question}\nA: ${t.answer}`).join("\n"),
    [turns],
  );

  function handleSend() {
    if (!draft.trim() || currentPrompt === null) return;
    setTurns((prev) => [...prev, { question: currentPrompt, answer: draft.trim() }]);
    setDraft("");
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
        {currentPrompt ? <ChatBubble role="assistant">{currentPrompt}</ChatBubble> : null}
      </div>

      {!finished ? (
        <div className="mt-4 flex items-center gap-2">
          <Input
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") handleSend();
            }}
            placeholder="話すように入力してください"
          />
          <Button size="icon" aria-label="Send" disabled={!draft.trim()} onClick={handleSend}>
            <Send size={16} />
          </Button>
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
            disabled={submit.isPending || !workspaceId}
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
