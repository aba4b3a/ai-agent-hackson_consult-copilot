"use client";

import { useMemo, useState } from "react";

import { BottomNav } from "@/components/feature/discovery/BottomNav";
import { Card } from "@/components/ui/Card";
import { LoadingState } from "@/components/ui/LoadingState";
import { PhoneFrame } from "@/components/ui/PhoneFrame";
import { useApprovalList, useApproveApproval, useRejectApproval } from "@/hooks/use-approvals";
import type { ApprovalRecord, ApprovalStatus } from "@/services/approval-service";

const STATUS_LABELS: Record<ApprovalStatus, string> = {
  pending: "未承認",
  approved: "承認済",
  rejected: "却下",
  applied: "反映済",
  cancelled: "取消",
};

const TARGET_LABELS: Record<string, string> = {
  kpi_candidate: "KPI候補",
  focus_metric_candidate: "重点管理指標候補",
  custom_table: "カスタム表",
  wiki_update: "Wiki更新",
  schema_migration: "スキーマ変更",
  observation_signal: "観測シグナル",
  other: "その他",
};

const StatusFilter = ({
  value,
  onChange,
}: {
  value: ApprovalStatus | undefined;
  onChange: (next: ApprovalStatus | undefined) => void;
}) => {
  const options: { label: string; value: ApprovalStatus | undefined }[] = [
    { label: "未承認", value: "pending" },
    { label: "承認済", value: "approved" },
    { label: "却下", value: "rejected" },
    { label: "反映済", value: "applied" },
    { label: "全て", value: undefined },
  ];
  return (
    <div className="flex flex-wrap gap-2">
      {options.map((option) => {
        const active = value === option.value;
        return (
          <button
            key={option.label}
            type="button"
            onClick={() => onChange(option.value)}
            className={`rounded-full px-3 py-1 text-xs font-black transition ${
              active ? "bg-blue-600 text-white" : "bg-slate-100 text-slate-600"
            }`}
          >
            {option.label}
          </button>
        );
      })}
    </div>
  );
};

const ApprovalDetail = ({
  record,
  decidedBy,
  onChangeDecidedBy,
  note,
  onChangeNote,
  onApprove,
  onReject,
  pending,
}: {
  record: ApprovalRecord;
  decidedBy: string;
  onChangeDecidedBy: (value: string) => void;
  note: string;
  onChangeNote: (value: string) => void;
  onApprove: () => void;
  onReject: () => void;
  pending: boolean;
}) => {
  const isActionable = record.status === "pending";
  return (
    <Card className="mt-4 space-y-3 rounded-lg">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <p className="text-[11px] font-black uppercase tracking-wide text-blue-600">
            {TARGET_LABELS[record.target_type] ?? record.target_type}
          </p>
          <h2 className="mt-1 text-sm font-black leading-snug text-slate-950">{record.title}</h2>
        </div>
        <span
          className={`rounded-full px-3 py-1 text-[11px] font-black ${
            record.status === "pending"
              ? "bg-amber-50 text-amber-700"
              : record.status === "approved"
                ? "bg-teal-50 text-teal-700"
                : record.status === "applied"
                  ? "bg-blue-50 text-blue-700"
                  : "bg-slate-100 text-slate-600"
          }`}
        >
          {STATUS_LABELS[record.status]}
        </span>
      </div>
      <p className="text-xs font-semibold leading-relaxed text-slate-600">{record.summary}</p>
      {record.reason ? <p className="text-xs font-bold text-slate-500">理由: {record.reason}</p> : null}
      {typeof record.confidence === "number" ? (
        <p className="text-xs font-bold text-slate-500">確度: {(record.confidence * 100).toFixed(0)}%</p>
      ) : null}
      <details className="rounded-lg border border-slate-200 bg-white p-3">
        <summary className="cursor-pointer text-xs font-black text-slate-700">提案内容(JSON)</summary>
        <pre className="mt-2 max-h-72 overflow-auto text-[11px] leading-relaxed text-slate-700">
          {JSON.stringify(record.proposed_payload, null, 2)}
        </pre>
      </details>
      {record.diff_payload ? (
        <details className="rounded-lg border border-slate-200 bg-white p-3">
          <summary className="cursor-pointer text-xs font-black text-slate-700">差分(JSON)</summary>
          <pre className="mt-2 max-h-72 overflow-auto text-[11px] leading-relaxed text-slate-700">
            {JSON.stringify(record.diff_payload, null, 2)}
          </pre>
        </details>
      ) : null}

      {isActionable ? (
        <div className="space-y-2 rounded-lg bg-slate-50 p-3">
          <label className="block text-[11px] font-black text-slate-600">承認者ID/メール</label>
          <input
            className="w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm font-semibold outline-none focus:border-blue-500"
            value={decidedBy}
            onChange={(event) => onChangeDecidedBy(event.target.value)}
            placeholder="reviewer@example.com"
          />
          <label className="block text-[11px] font-black text-slate-600">コメント(任意)</label>
          <textarea
            className="min-h-16 w-full resize-y rounded-md border border-slate-200 bg-white px-3 py-2 text-sm font-semibold outline-none focus:border-blue-500"
            value={note}
            onChange={(event) => onChangeNote(event.target.value)}
            placeholder="判断理由・条件など"
          />
          <div className="flex gap-2">
            <button
              type="button"
              className="flex-1 rounded-full bg-teal-600 px-4 py-2 text-sm font-black text-white disabled:bg-slate-300"
              disabled={!decidedBy.trim() || pending}
              onClick={onApprove}
            >
              承認
            </button>
            <button
              type="button"
              className="flex-1 rounded-full bg-rose-600 px-4 py-2 text-sm font-black text-white disabled:bg-slate-300"
              disabled={!decidedBy.trim() || pending}
              onClick={onReject}
            >
              却下
            </button>
          </div>
        </div>
      ) : (
        <div className="rounded-lg bg-slate-50 p-3 text-[11px] font-bold text-slate-600">
          {record.decided_by ? <p>判定者: {record.decided_by}</p> : null}
          {record.decided_at ? <p>判定日時: {record.decided_at}</p> : null}
          {record.decision_note ? <p>メモ: {record.decision_note}</p> : null}
        </div>
      )}
    </Card>
  );
};

export const ApprovalsList = () => {
  const [statusFilter, setStatusFilter] = useState<ApprovalStatus | undefined>("pending");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [decidedBy, setDecidedBy] = useState("");
  const [note, setNote] = useState("");

  const { data, isLoading, isError } = useApprovalList(statusFilter);
  const approveMutation = useApproveApproval();
  const rejectMutation = useRejectApproval();

  const selected = useMemo(
    () => data?.items.find((item) => item.approval_id === selectedId) ?? null,
    [data?.items, selectedId],
  );

  if (isLoading) return <LoadingState message="承認待ち項目を読込中..." active="approvals" />;
  if (isError || !data) return <LoadingState isError message="承認データを取得できませんでした。" active="approvals" />;

  return (
    <PhoneFrame>
      <div className="px-5 pb-24 pt-5 md:px-7 md:pb-8 md:pt-8">
        <header className="space-y-1">
          <p className="text-xs font-black text-blue-600">Human-in-the-loop</p>
          <h1 className="text-xl font-black tracking-tight text-slate-950 md:text-2xl">承認キュー</h1>
          <p className="text-xs font-bold text-slate-500">
            KPI候補・重点指標・Wiki更新・スキーマ変更などをここで承認します。承認後にBigQueryおよびWikiの本番定義が更新されます。
          </p>
        </header>

        <section className="mt-4 space-y-3">
          <StatusFilter
            value={statusFilter}
            onChange={(next) => {
              setStatusFilter(next);
              setSelectedId(null);
            }}
          />
          <p className="text-[11px] font-bold text-slate-500">{data.total} 件</p>
        </section>

        <section className="mt-2 space-y-2">
          {data.items.length === 0 ? (
            <Card className="rounded-lg p-4 text-xs font-bold text-slate-500">対象の項目はありません。</Card>
          ) : (
            data.items.map((item) => (
              <button
                key={item.approval_id}
                type="button"
                className={`w-full rounded-lg border px-3 py-3 text-left transition ${
                  item.approval_id === selectedId
                    ? "border-blue-500 bg-blue-50"
                    : "border-slate-200 bg-white hover:border-slate-300"
                }`}
                onClick={() => setSelectedId(item.approval_id)}
              >
                <div className="flex items-center justify-between gap-3">
                  <span className="text-[11px] font-black uppercase tracking-wide text-slate-500">
                    {TARGET_LABELS[item.target_type] ?? item.target_type}
                  </span>
                  <span className="text-[10px] font-bold text-slate-400">{item.created_at.slice(0, 16)}</span>
                </div>
                <p className="mt-1 text-sm font-black text-slate-950">{item.title}</p>
                <p className="mt-0.5 text-[11px] font-semibold text-slate-500">{item.summary || ""}</p>
              </button>
            ))
          )}
        </section>

        {selected ? (
          <ApprovalDetail
            record={selected}
            decidedBy={decidedBy}
            onChangeDecidedBy={setDecidedBy}
            note={note}
            onChangeNote={setNote}
            pending={approveMutation.isPending || rejectMutation.isPending}
            onApprove={() =>
              approveMutation.mutate({
                approvalId: selected.approval_id,
                decidedBy: decidedBy.trim(),
                note: note.trim() || undefined,
              })
            }
            onReject={() =>
              rejectMutation.mutate({
                approvalId: selected.approval_id,
                decidedBy: decidedBy.trim(),
                note: note.trim() || undefined,
              })
            }
          />
        ) : null}

        {approveMutation.isError || rejectMutation.isError ? (
          <div className="mt-3 rounded-lg bg-rose-50 px-3 py-2 text-xs font-black text-rose-700">
            処理に失敗しました。
          </div>
        ) : null}
      </div>
      <BottomNav active="approvals" />
    </PhoneFrame>
  );
};
