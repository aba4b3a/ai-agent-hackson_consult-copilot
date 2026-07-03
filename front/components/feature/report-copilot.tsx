"use client";

import { useState } from "react";
import { Bot, X } from "lucide-react";

import { useCopilot } from "@/hooks/use-copilot";
import { Button } from "@/components/ui/button";
import { Pill } from "@/components/ui/pill";
import { useToast } from "@/components/ui/toast";

const SUGGESTED = [
  "なぜ価格・待ち時間関連の発言が増えた？",
  "どの顧客セグメントで変化が大きい？",
  "来週何を観測すべき？",
];

/**
 * Report Copilot as a fixed bottom-right assistant: a FAB that expands into a
 * chat panel. Grounded answers keep observed facts / hypotheses / evidence
 * separated (R16).
 */
export function ReportCopilot({ workspaceId }: { workspaceId: string }) {
  const [open, setOpen] = useState(false);
  const [question, setQuestion] = useState(SUGGESTED[0]);
  const copilot = useCopilot(workspaceId);
  const toast = useToast();
  const answer = copilot.data;

  function handleAsk() {
    copilot.mutate(question, {
      onError: () => toast({ message: "回答の生成に失敗しました。", tone: "danger" }),
    });
  }

  if (!open) {
    return (
      <button
        type="button"
        aria-label="Open Report Copilot"
        onClick={() => setOpen(true)}
        className="fixed bottom-4 right-4 z-20 grid h-14 w-14 place-items-center rounded-full bg-accent text-accent-foreground shadow-lg hover:opacity-90"
      >
        <Bot size={24} />
      </button>
    );
  }

  return (
    <div className="fixed bottom-4 right-4 z-20 flex max-h-[70vh] w-[min(400px,calc(100vw-2rem))] flex-col overflow-hidden rounded-card border border-border bg-surface shadow-lg">
      <div className="flex items-center justify-between border-b border-border px-4 py-3">
        <div className="flex items-center gap-2">
          <Bot size={18} />
          <h2 className="text-sm font-semibold">Report Copilot</h2>
        </div>
        <button
          type="button"
          aria-label="Close Report Copilot"
          onClick={() => setOpen(false)}
          className="grid h-8 w-8 place-items-center rounded-md text-text-muted hover:bg-background"
        >
          <X size={16} />
        </button>
      </div>

      <div className="overflow-y-auto p-4">
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
          onClick={handleAsk}
        >
          {copilot.isPending ? "回答生成中…" : "Ask copilot"}
        </Button>

        {answer ? (
          <div className="mt-4 space-y-4">
            <p className="text-sm leading-6 text-text">{answer.answer}</p>

            {answer.observed_facts.length > 0 ? (
              <div>
                <p className="text-xs font-medium uppercase tracking-[0.12em] text-text-muted">
                  観察事実
                </p>
                <ul className="mt-2 space-y-1.5">
                  {answer.observed_facts.map((f) => (
                    <li key={f} className="text-sm leading-6 text-text">
                      {f}
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}

            {answer.hypotheses.length > 0 ? (
              <div>
                <p className="text-xs font-medium uppercase tracking-[0.12em] text-text-muted">
                  仮説
                </p>
                <ul className="mt-2 space-y-1.5">
                  {answer.hypotheses.map((h) => (
                    <li key={h} className="flex items-start gap-2 text-sm leading-6 text-text">
                      <Pill tone="warning">仮説</Pill>
                      <span>{h}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}

            {answer.evidence.length > 0 ? (
              <div>
                <p className="text-xs font-medium uppercase tracking-[0.12em] text-text-muted">
                  証拠
                </p>
                <div className="mt-2 space-y-2">
                  {answer.evidence.map((e) => (
                    <article key={e.source_id} className="border-t border-border pt-2">
                      <p className="text-xs text-text-muted">{e.source_type}</p>
                      <p className="text-sm leading-6 text-text">{e.snippet}</p>
                    </article>
                  ))}
                </div>
              </div>
            ) : null}

            {answer.recommended_observations.length > 0 ? (
              <div>
                <p className="text-xs font-medium uppercase tracking-[0.12em] text-text-muted">
                  推奨観測
                </p>
                <ul className="mt-2 list-disc space-y-1 pl-5">
                  {answer.recommended_observations.map((r) => (
                    <li key={r} className="text-sm leading-6 text-text-muted">
                      {r}
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
          </div>
        ) : null}
      </div>
    </div>
  );
}
