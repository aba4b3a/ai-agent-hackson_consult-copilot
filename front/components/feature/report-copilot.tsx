"use client";

import { useState } from "react";
import { Bot } from "lucide-react";

import { useCopilot } from "@/hooks/use-copilot";
import { Button } from "@/components/ui/button";
import { Card, Section } from "@/components/ui/card";
import { Pill } from "@/components/ui/pill";

const SUGGESTED = [
  "なぜ価格・待ち時間関連の発言が増えた？",
  "どの顧客セグメントで変化が大きい？",
  "来週何を観測すべき？",
];

export function ReportCopilot({ workspaceId }: { workspaceId: string }) {
  const [question, setQuestion] = useState(SUGGESTED[0]);
  const copilot = useCopilot(workspaceId);
  const answer = copilot.data;

  return (
    <Section title="Report Copilot" icon={<Bot size={18} />}>
      <Card>
        <div className="flex flex-wrap gap-1.5">
          {SUGGESTED.map((item) => (
            <button key={item} type="button" onClick={() => setQuestion(item)}>
              <Pill>{item}</Pill>
            </button>
          ))}
        </div>

        <label className="mt-3 block">
          <textarea
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            rows={2}
            className="w-full resize-none rounded-md border border-border bg-surface px-3 py-2 text-sm text-text outline-none"
          />
        </label>
        <Button
          className="mt-3 w-full"
          disabled={copilot.isPending || !question.trim()}
          onClick={() => copilot.mutate(question)}
        >
          {copilot.isPending ? "回答生成中…" : "Ask copilot"}
        </Button>

        {answer ? (
          <div className="mt-4 space-y-3">
            <p className="text-sm leading-6 text-text">{answer.answer}</p>
            {answer.hypotheses.length > 0 ? (
              <div className="flex flex-wrap gap-1.5">
                {answer.hypotheses.map((h) => (
                  <Pill key={h} tone="warning">
                    仮説
                  </Pill>
                ))}
              </div>
            ) : null}
          </div>
        ) : null}
      </Card>
    </Section>
  );
}
