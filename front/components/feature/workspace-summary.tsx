"use client";

import Link from "next/link";
import { Link2, MessageSquarePlus } from "lucide-react";

import { useDashboard } from "@/hooks/use-dashboard";
import { useCreateReportForm } from "@/hooks/use-create-report-form";
import { Button } from "@/components/ui/button";
import { MetricCard } from "@/components/ui/metric-card";
import { Pill } from "@/components/ui/pill";
import { Skeleton } from "@/components/ui/skeleton";

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
  const createForm = useCreateReportForm();
  const intakePath = createForm.data ? `/intake?form=${createForm.data.form_id}` : null;

  if (isLoading || !data) {
    return (
      <section id="summary" className="scroll-mt-20 space-y-5">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-4 w-full max-w-2xl" />
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          {[0, 1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-28" />
          ))}
        </div>
      </section>
    );
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
    <section id="summary" className="scroll-mt-20 space-y-5">
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
          <Button
            disabled={createForm.isPending || !workspaceId}
            onClick={() => createForm.mutate({ workspace_id: workspaceId })}
          >
            <Link2 size={16} />
            {createForm.isPending ? "生成中…" : "Intake link"}
          </Button>
          <Link href={`/intake/chat?ws=${workspaceId}`} aria-label="Conversational intake">
            <Button variant="outline" size="icon">
              <MessageSquarePlus size={17} />
            </Button>
          </Link>
        </div>
      </div>

      {intakePath ? (
        <div className="flex flex-wrap items-center gap-2 rounded-md border border-border bg-surface p-3">
          <Pill tone="success">共有リンク</Pill>
          <Link href={intakePath} className="text-sm text-accent underline">
            {intakePath}
          </Link>
          <span className="text-xs text-text-muted">業務側に共有して日報を集めます</span>
        </div>
      ) : null}

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">{tiles}</div>
    </section>
  );
}
