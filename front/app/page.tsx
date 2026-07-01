"use client";

import { Search } from "lucide-react";

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
  const workspaceId = workspaces?.[0]?.workspace_id ?? "";

  return (
    <AppShell
      header={
        <Header
          eyebrow="Continuous Discovery Agent"
          title="Consultant Copilot"
          trailing={
            <Button variant="outline" size="icon" aria-label="Search">
              <Search size={18} />
            </Button>
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
