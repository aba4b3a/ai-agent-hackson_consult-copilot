"use client";

import { MessageSquareText, RefreshCw } from "lucide-react";

import { useGenerateWeeklyReport, useWeeklyReport } from "@/hooks/use-weekly-report";
import { Button } from "@/components/ui/button";
import { Card, Section } from "@/components/ui/card";
import { Pill } from "@/components/ui/pill";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/components/ui/toast";

export function WeeklyReport({ workspaceId }: { workspaceId: string }) {
  const { data, isLoading } = useWeeklyReport(workspaceId);
  const generate = useGenerateWeeklyReport(workspaceId);
  const toast = useToast();

  function handleGenerate() {
    generate.mutate(undefined, {
      onSuccess: () => toast({ message: "レポートを再生成しました。", tone: "success" }),
      onError: () => toast({ message: "レポートの再生成に失敗しました。", tone: "danger" }),
    });
  }

  return (
    <Section id="report" title="Weekly Report" icon={<MessageSquareText size={18} />}>
      <Card>
        {isLoading || generate.isPending ? (
          <div className="space-y-2">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-5/6" />
            <Skeleton className="h-3 w-40" />
          </div>
        ) : (
          <p className="text-sm leading-6 text-text">{data?.summary}</p>
        )}
        {data?.period ? <p className="mt-2 text-xs text-text-muted">{data.period}</p> : null}

        {data && data.recommended_observations.length > 0 ? (
          <div className="mt-4">
            <p className="text-xs font-medium uppercase tracking-[0.12em] text-text-muted">
              次週の推奨観測
            </p>
            <ul className="mt-2 list-disc space-y-1 pl-5">
              {data.recommended_observations.map((item) => (
                <li key={item} className="text-sm leading-6 text-text-muted">
                  {item}
                </li>
              ))}
            </ul>
          </div>
        ) : null}
        <div className="mt-4 grid gap-2">
          <Pill tone="success">Facts separated</Pill>
          <Pill tone="warning">Hypotheses labeled</Pill>
          <Pill>Evidence linked</Pill>
        </div>

        {data?.limitations && data.limitations.length > 0 ? (
          <div className="mt-4 border-t border-border pt-3">
            <p className="text-xs font-medium uppercase tracking-[0.12em] text-text-muted">
              Limitations
            </p>
            <ul className="mt-2 space-y-1.5">
              {data.limitations.map((item) => (
                <li key={item} className="text-xs leading-5 text-text-muted">
                  {item}
                </li>
              ))}
            </ul>
          </div>
        ) : null}

        <Button
          variant="outline"
          className="mt-4 w-full"
          disabled={generate.isPending || !workspaceId}
          onClick={handleGenerate}
        >
          <RefreshCw size={16} />
          {generate.isPending ? "生成中…" : "レポートを再生成"}
        </Button>
      </Card>
    </Section>
  );
}
