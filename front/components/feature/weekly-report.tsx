"use client";

import { MessageSquareText } from "lucide-react";

import { useWeeklyReport } from "@/hooks/use-weekly-report";
import { Card, Section } from "@/components/ui/card";
import { Pill } from "@/components/ui/pill";

export function WeeklyReport({ workspaceId }: { workspaceId: string }) {
  const { data } = useWeeklyReport(workspaceId);

  return (
    <Section title="Weekly Report" icon={<MessageSquareText size={18} />}>
      <Card>
        <p className="text-sm leading-6 text-text">
          {data?.summary ?? "レポートを読み込み中…"}
        </p>
        {data?.period ? <p className="mt-2 text-xs text-text-muted">{data.period}</p> : null}
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
      </Card>
    </Section>
  );
}
