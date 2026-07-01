"use client";

import { Suspense } from "react";
import { useSearchParams } from "next/navigation";

import { AppShell } from "@/components/ui/app-shell";
import { Card } from "@/components/ui/card";
import { Header } from "@/components/ui/header";
import { ReportForm } from "@/components/feature/report-form";

/**
 * Business-side URL report form. Standalone view — deliberately shows no
 * consultant dashboard/search/graph features (R2, tasks §16.1). The form id is
 * read from the `?form=` query param (static-export friendly).
 */
function IntakeContent() {
  const formId = useSearchParams().get("form") ?? "";

  return (
    <div className="mx-auto max-w-2xl space-y-4">
      <p className="text-sm leading-6 text-text-muted">
        今日の気づきを共有してください。短い入力でも役立ちます。
      </p>
      {formId ? (
        <ReportForm formId={formId} />
      ) : (
        <Card>フォームIDが指定されていません。共有されたリンクからアクセスしてください。</Card>
      )}
    </div>
  );
}

export default function IntakePage() {
  return (
    <AppShell header={<Header title="日報フォーム" />}>
      <Suspense fallback={<div className="mx-auto max-w-2xl text-sm text-text-muted">読み込み中…</div>}>
        <IntakeContent />
      </Suspense>
    </AppShell>
  );
}
