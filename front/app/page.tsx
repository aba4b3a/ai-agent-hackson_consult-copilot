"use client";

import { useState } from "react";
import Link from "next/link";
import { Menu, Settings } from "lucide-react";

import { useWorkspaces } from "@/hooks/use-workspaces";
import { AppShell } from "@/components/ui/app-shell";
import { Button } from "@/components/ui/button";
import { Header } from "@/components/ui/header";
import { Sidebar } from "@/components/ui/sidebar";
import { BusinessIntake } from "@/components/feature/business-intake";
import { DiscoveryFeed } from "@/components/feature/discovery-feed";
import { EvidenceSearch } from "@/components/feature/evidence-search";
import { GraphViewer } from "@/components/feature/graph-viewer";
import { KnowledgeFormation } from "@/components/feature/knowledge-formation";
import { ReportCopilot } from "@/components/feature/report-copilot";
import { WeeklyReport } from "@/components/feature/weekly-report";
import { WorkspaceSummary } from "@/components/feature/workspace-summary";

const SECTION_LINKS = [
  { label: "サマリ", href: "#summary" },
  { label: "Discovery Feed", href: "#discovery" },
  { label: "Knowledge Formation", href: "#knowledge" },
  { label: "Graph Viewer", href: "#graph" },
  { label: "Business Intake", href: "#intake" },
  { label: "Evidence Search", href: "#evidence" },
  { label: "Weekly Report", href: "#report" },
];

const PAGE_LINKS = [
  { label: "ワークスペース設定", href: "/setup" },
  { label: "会話形式の聞き取り", href: "/intake/chat" },
];

export default function HomePage() {
  const { data: workspaces } = useWorkspaces();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const workspaceId = selectedId ?? workspaces?.[0]?.workspace_id ?? "";

  return (
    <AppShell
      header={
        <Header
          leading={
            <Button
              variant="outline"
              size="icon"
              aria-label="Open navigation"
              className="lg:hidden"
              onClick={() => setSidebarOpen(true)}
            >
              <Menu size={18} />
            </Button>
          }
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
      <div className="flex gap-6">
        <Sidebar
          items={SECTION_LINKS}
          pages={PAGE_LINKS}
          open={sidebarOpen}
          onClose={() => setSidebarOpen(false)}
        />

        <div className="min-w-0 flex-1">
          <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
            <div className="space-y-6">
              <WorkspaceSummary workspaceId={workspaceId} />
              <DiscoveryFeed workspaceId={workspaceId} />
              <KnowledgeFormation workspaceId={workspaceId} />
            </div>

            <aside className="space-y-6">
              <GraphViewer workspaceId={workspaceId} />
              <BusinessIntake />
              <EvidenceSearch workspaceId={workspaceId} />
              <WeeklyReport workspaceId={workspaceId} />
            </aside>
          </div>
        </div>
      </div>

      {/* Fixed bottom-right assistant */}
      <ReportCopilot workspaceId={workspaceId} />
    </AppShell>
  );
}
