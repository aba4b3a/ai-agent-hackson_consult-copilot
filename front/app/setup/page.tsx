"use client";

import Link from "next/link";
import { ArrowLeft } from "lucide-react";

import { AppShell } from "@/components/ui/app-shell";
import { Header } from "@/components/ui/header";
import { Button } from "@/components/ui/button";
import { WorkspaceSetupForm } from "@/components/feature/workspace-setup-form";

export default function SetupPage() {
  return (
    <AppShell
      header={
        <Header
          eyebrow="Continuous Discovery Agent"
          title="ワークスペース設定"
          trailing={
            <Link href="/" aria-label="Back to dashboard">
              <Button variant="outline" size="icon">
                <ArrowLeft size={18} />
              </Button>
            </Link>
          }
        />
      }
    >
      <div className="mx-auto max-w-2xl space-y-4">
        <p className="text-sm leading-6 text-text-muted">
          クライアント企業の基本情報を登録します。後から観察データが集まると、この文脈をもとにナレッジが形成されます。
        </p>
        <WorkspaceSetupForm />
      </div>
    </AppShell>
  );
}
