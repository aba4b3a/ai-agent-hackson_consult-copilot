"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { useReportForm } from "@/hooks/use-report-form";
import { useSubmitReport } from "@/hooks/use-submit-report";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Field, Input, Textarea } from "@/components/ui/field";
import { useToast } from "@/components/ui/toast";

/**
 * Business-side daily report form (§4.2/4.3). Minimal required fields (only the
 * free-text note), the rest are optional and skippable (R2.6/R2.7). Guided
 * questions come from the form's observation policy.
 */
export function ReportForm({ formId }: { formId: string }) {
  const router = useRouter();
  const { data: form, isLoading, isError } = useReportForm(formId);
  const submit = useSubmitReport();
  const toast = useToast();

  const [freeText, setFreeText] = useState("");
  const [customerType, setCustomerType] = useState("");
  const [product, setProduct] = useState("");
  const [issue, setIssue] = useState("");
  const [competitor, setCompetitor] = useState("");
  const [kpiNote, setKpiNote] = useState("");

  if (isLoading) {
    return <Card>フォームを読み込み中…</Card>;
  }
  if (isError || !form) {
    return <Card>フォームが見つかりません。リンクをご確認ください。</Card>;
  }

  function handleSubmit() {
    submit.mutate(
      {
        form_id: formId,
        free_text: freeText.trim(),
        customer_type: customerType.trim() || "unknown",
        product: product.trim() || "unknown",
        issue_category: issue.trim() || "unknown",
        competitor: competitor.trim() || null,
        kpi_note: kpiNote.trim() || null,
      },
      {
        onSuccess: () => router.push("/"),
        onError: () => toast({ message: "送信に失敗しました。再試行してください。", tone: "danger" }),
      },
    );
  }

  return (
    <Card>
      {form.questions.length > 0 ? (
        <div className="mb-4 rounded-md border border-border bg-background p-3">
          <p className="text-xs font-medium uppercase tracking-[0.12em] text-text-muted">今日の質問</p>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-sm leading-6 text-text">
            {form.questions.map((q) => (
              <li key={q}>{q}</li>
            ))}
          </ul>
        </div>
      ) : null}

      <div className="space-y-4">
        <Field label="気づいたこと・顧客の声" htmlFor="rf-text" hint="短くてOK。まずはこれだけでも送れます。">
          <Textarea
            id="rf-text"
            rows={4}
            value={freeText}
            onChange={(e) => setFreeText(e.target.value)}
            placeholder="例: 高齢のお客様から、駅前ドラッグのほうが待ち時間が短いと言われた。"
          />
        </Field>
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="顧客層" htmlFor="rf-customer" optional>
            <Input id="rf-customer" value={customerType} onChange={(e) => setCustomerType(e.target.value)} placeholder="高齢者" />
          </Field>
          <Field label="商品・サービス" htmlFor="rf-product" optional>
            <Input id="rf-product" value={product} onChange={(e) => setProduct(e.target.value)} placeholder="処方箋受付" />
          </Field>
          <Field label="課題カテゴリ" htmlFor="rf-issue" optional>
            <Input id="rf-issue" value={issue} onChange={(e) => setIssue(e.target.value)} placeholder="待ち時間" />
          </Field>
          <Field label="競合名" htmlFor="rf-competitor" optional>
            <Input id="rf-competitor" value={competitor} onChange={(e) => setCompetitor(e.target.value)} placeholder="駅前ドラッグ" />
          </Field>
        </div>
        <Field label="KPIメモ" htmlFor="rf-kpi" optional>
          <Input id="rf-kpi" value={kpiNote} onChange={(e) => setKpiNote(e.target.value)} placeholder="夕方の待ち時間が伸びた" />
        </Field>

        {submit.isError ? (
          <p className="text-sm text-danger">送信に失敗しました。時間をおいて再試行してください。</p>
        ) : null}

        <Button className="w-full" disabled={submit.isPending || !freeText.trim()} onClick={handleSubmit}>
          {submit.isPending ? "送信中…" : "送信"}
        </Button>
      </div>
    </Card>
  );
}
