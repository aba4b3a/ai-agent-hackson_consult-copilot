"use client";

import { useState } from "react";
import { GitBranch } from "lucide-react";

import { useGraphSlice } from "@/hooks/use-graph-slice";
import { Card, Section } from "@/components/ui/card";
import { GraphCard } from "@/components/ui/graph-card";
import { PillTabs } from "@/components/ui/pill-tabs";

const GRAPH_TABS = ["Customer x Issue", "Competitor Impact", "KPI Causal", "Hypothesis", "Gap Graph"];

export function GraphViewer({ workspaceId }: { workspaceId: string }) {
  const [tab, setTab] = useState(GRAPH_TABS[0]);
  const { data } = useGraphSlice(workspaceId);

  return (
    <Section title="Graph Viewer" icon={<GitBranch size={18} />}>
      <Card>
        <PillTabs tabs={GRAPH_TABS} value={tab} onChange={setTab} className="mb-4" />
        <GraphCard nodes={data?.nodes ?? []} edges={data?.edges ?? []} />
        {data?.summary ? (
          <p className="mt-3 text-sm leading-6 text-text-muted">{data.summary}</p>
        ) : null}
      </Card>
    </Section>
  );
}
