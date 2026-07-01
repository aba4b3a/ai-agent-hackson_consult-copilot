"use client";

import { AudioLines } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, Section } from "@/components/ui/card";
import { ChatBubble } from "@/components/ui/chat-bubble";

/**
 * Business-side conversational intake preview. Presentational for M1 — the live
 * voice/transcription flow is a later milestone (tasks §5).
 */
export function BusinessIntake() {
  return (
    <Section title="Business Intake" icon={<AudioLines size={18} />}>
      <Card>
        <div className="space-y-3">
          <ChatBubble role="assistant">今日、顧客から普段と違う反応や相談はありましたか。</ChatBubble>
          <ChatBubble role="user">子育て世帯からオンライン服薬指導の相談が増えました。</ChatBubble>
          <ChatBubble role="assistant">どの時間帯、商品、競合名と関係していましたか。</ChatBubble>
        </div>
        <Button className="mt-4 w-full">
          <AudioLines size={16} />
          Simulate voice intake
        </Button>
      </Card>
    </Section>
  );
}
