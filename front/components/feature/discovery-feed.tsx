"use client";

import { Sparkles } from "lucide-react";

import { useDashboard } from "@/hooks/use-dashboard";
import type { PillProps } from "@/components/ui/pill";
import { Pill } from "@/components/ui/pill";
import { ListItem } from "@/components/ui/list-item";
import { Section } from "@/components/ui/card";

function severityTone(severity: string): NonNullable<PillProps["tone"]> {
  if (severity === "danger") return "danger";
  if (severity === "warning") return "warning";
  return "info";
}

export function DiscoveryFeed({ workspaceId }: { workspaceId: string }) {
  const { data } = useDashboard(workspaceId);
  const signals = data?.signals ?? [];

  return (
    <Section id="discovery" title="Discovery Feed" icon={<Sparkles size={18} />}>
      <div className="space-y-3">
        {signals.map((signal) => (
          <ListItem
            key={signal.signal_id}
            title={signal.metric_name}
            detail={`${signal.related_entities.join(" / ")}（${signal.baseline_value} → ${signal.current_value}）`}
            trailing={<Pill tone={severityTone(signal.severity)}>{signal.evidence_count} evidence</Pill>}
          />
        ))}
        {signals.length === 0 ? (
          <p className="text-sm text-text-muted">シグナルはまだありません。</p>
        ) : null}
      </div>
    </Section>
  );
}
