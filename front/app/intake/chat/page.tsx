"use client";

import { Suspense } from "react";
import { useSearchParams } from "next/navigation";

import { AppShell } from "@/components/ui/app-shell";
import { Header } from "@/components/ui/header";
import { VoiceChatIntake } from "@/components/feature/voice-chat-intake";

/**
 * Business-side conversational (text) intake. Standalone view like /intake.
 * Workspace id is read from `?ws=`.
 */
function ChatContent() {
  const workspaceId = useSearchParams().get("ws") ?? "";

  return (
    <div className="mx-auto max-w-2xl space-y-4">
      <p className="text-sm leading-6 text-text-muted">
        質問に沿って、話すように入力してください。順番に伺います。
      </p>
      <VoiceChatIntake workspaceId={workspaceId} />
    </div>
  );
}

export default function IntakeChatPage() {
  return (
    <AppShell header={<Header title="会話形式の聞き取り" />}>
      <Suspense fallback={<div className="mx-auto max-w-2xl text-sm text-text-muted">読み込み中…</div>}>
        <ChatContent />
      </Suspense>
    </AppShell>
  );
}
