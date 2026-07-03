"use client";

import { useState } from "react";
import { GitBranch } from "lucide-react";

import { useGraphSlice } from "@/hooks/use-graph-slice";
import type { GraphView } from "@/services/discovery-service";
import { Card, Section } from "@/components/ui/card";
import { GraphCard } from "@/components/ui/graph-card";
import { PillTabs } from "@/components/ui/pill-tabs";
import { Skeleton } from "@/components/ui/skeleton";

// Tab label -> API view key. Gap Graph (knowledge-gap view) is a follow-up.
const GRAPH_TABS: Record<string, GraphView> = {
  "Customer × Issue": "customer-issue",
  "Competitor Impact": "competitor-impact",
  "KPI Causal": "kpi-causal",
  Hypothesis: "hypothesis",
};
const TAB_LABELS = Object.keys(GRAPH_TABS);

export function GraphViewer({ workspaceId }: { workspaceId: string }) {
  const [tab, setTab] = useState(TAB_LABELS[0]);
  const { data, isLoading } = useGraphSlice(workspaceId, GRAPH_TABS[tab]);

  return (
    <Section id="graph" title="Graph Viewer" icon={<GitBranch size={18} />}>
      <Card>
        <PillTabs tabs={TAB_LABELS} value={tab} onChange={setTab} className="mb-4" />
        {isLoading ? (
          <Skeleton className="h-72" />
        ) : !data || data.nodes.length === 0 ? (
          <div className="grid h-72 place-items-center rounded-md border border-border bg-background">
            <p className="text-sm text-text-muted">
              この視点で表示できる観察データがまだ不足しています。
            </p>
          </div>
        ) : (
          <GraphCard nodes={data.nodes} edges={data.edges} />
        )}
        {data?.summary ? (
          <p className="mt-3 text-sm leading-6 text-text-muted">{data.summary}</p>
        ) : null}
      </Card>
    </Section>
  );
}
