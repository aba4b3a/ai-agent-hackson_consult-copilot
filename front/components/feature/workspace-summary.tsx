"use client";

import { Link2, PenLine } from "lucide-react";

import { useDashboard } from "@/hooks/use-dashboard";
import { Button } from "@/components/ui/button";
import { MetricCard } from "@/components/ui/metric-card";

const METRIC_LABELS: Record<string, string> = {
  sources_ingested: "Sources",
  observations_extracted: "Facts",
  entities_formed: "Entities",
  hypotheses_under_observation: "Hypotheses",
};

const METRIC_CAPTIONS: Record<string, string> = {
  sources_ingested: "日報・音声・競合情報などの取り込み数",
  observations_extracted: "仮説と分離された観察事実",
  entities_formed: "セグメント・商品・課題・競合・KPI",
  hypotheses_under_observation: "観察中の仮説",
};

export function WorkspaceSummary({ workspaceId }: { workspaceId: string }) {
  const { data, isLoading } = useDashboard(workspaceId);

  if (isLoading || !data) {
    return <p className="text-sm text-text-muted">ワークスペースを読み込み中…</p>;
  }

  const { workspace, metrics } = data;
  const tiles = (
    ["sources_ingested", "observations_extracted", "entities_formed", "hypotheses_under_observation"] as const
  ).map((key) => (
    <MetricCard
      key={key}
      label={METRIC_LABELS[key]}
      value={metrics[key]}
      caption={METRIC_CAPTIONS[key]}
    />
  ));

  return (
    <section className="space-y-5">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-sm text-text-muted">Active workspace</p>
          <h2 className="mt-1 text-2xl font-semibold">{workspace.workspace_name}</h2>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-text-muted">
            {workspace.business_description ||
              "日報、音声入力、競合情報、KPIを継続的に集め、観察事実・仮説・証拠を分けて週次レポートにまとめます。"}
          </p>
        </div>
        <div className="flex gap-2">
          <Button>
            <Link2 size={16} />
            Intake link
          </Button>
          <Button variant="outline" size="icon" aria-label="Add note">
            <PenLine size={17} />
          </Button>
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">{tiles}</div>
    </section>
  );
}
