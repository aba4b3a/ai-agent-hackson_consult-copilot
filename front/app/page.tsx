"use client";

import { useState } from "react";
import Link from "next/link";
import { Settings } from "lucide-react";

import { useWorkspaces } from "@/hooks/use-workspaces";
import { AppShell } from "@/components/ui/app-shell";
import { Button } from "@/components/ui/button";
import { Header } from "@/components/ui/header";
import { BusinessIntake } from "@/components/feature/business-intake";
import { DiscoveryFeed } from "@/components/feature/discovery-feed";
import { EvidenceSearch } from "@/components/feature/evidence-search";
import { GraphViewer } from "@/components/feature/graph-viewer";
import { KnowledgeFormation } from "@/components/feature/knowledge-formation";
import { ReportCopilot } from "@/components/feature/report-copilot";
import { WeeklyReport } from "@/components/feature/weekly-report";
import { WorkspaceSummary } from "@/components/feature/workspace-summary";

export default function HomePage() {
  const { data: workspaces } = useWorkspaces();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const workspaceId = selectedId ?? workspaces?.[0]?.workspace_id ?? "";

  return (
    <AppShell
      header={
        <Header
          eyebrow="Continuous Discovery Agent"
          title="Consultant Copilot"
          trailing={
            <div className="flex items-center gap-2">
              {workspaces && workspaces.length > 0 ? (
                <select
                  value={workspaceId}
                  onChange={(e) => setSelectedId(e.target.value)}
                  aria-label="Select workspace"
                  className="rounded-md border border-border bg-surface px-2 py-2 text-sm text-text outline-none"
                >
                  {workspaces.map((ws) => (
                    <option key={ws.workspace_id} value={ws.workspace_id}>
                      {ws.workspace_name}
                    </option>
                  ))}
                </select>
              ) : null}
              <Link href="/setup" aria-label="Workspace setup">
                <Button variant="outline" size="icon">
                  <Settings size={18} />
                </Button>
              </Link>
            </div>
          }
        />
      }
    >
      <div className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
        <div className="space-y-6">
          <WorkspaceSummary workspaceId={workspaceId} />
          <DiscoveryFeed workspaceId={workspaceId} />
          <KnowledgeFormation workspaceId={workspaceId} />
          <GraphViewer workspaceId={workspaceId} />
        </div>

        <aside className="space-y-6 lg:sticky lg:top-20 lg:self-start">
          <BusinessIntake />
          <EvidenceSearch workspaceId={workspaceId} />
          <WeeklyReport workspaceId={workspaceId} />
          <ReportCopilot workspaceId={workspaceId} />
        </aside>
      </div>
    </AppShell>
  );
}
