"use client";

import { useState } from "react";

import { BottomNav } from "@/components/feature/discovery/BottomNav";
import { Card } from "@/components/ui/Card";
import { LoadingState } from "@/components/ui/LoadingState";
import { PhoneFrame } from "@/components/ui/PhoneFrame";
import { useAssignments, useSubmitFollowupAnswer } from "@/hooks/use-research";

const ROLES = [
  { value: "owner", label: "経営者" },
  { value: "manager", label: "管理者" },
  { value: "sales", label: "営業" },
  { value: "staff", label: "現場" },
];

export const ResearchInbox = () => {
  const [role, setRole] = useState("sales");
  const { data, isLoading, isError } = useAssignments({ targetRole: role, status: "open" });
  const submit = useSubmitFollowupAnswer();
  const [drafts, setDrafts] = useState<Record<string, string>>({});

  if (isLoading) return <LoadingState message="質問を読込中..." active="research" />;
  if (isError || !data) return <LoadingState isError message="Research Agent からの質問を取得できませんでした。" active="research" />;

  return (
    <PhoneFrame>
      <div className="px-5 pb-24 pt-5 md:px-7 md:pb-8 md:pt-8">
        <header className="space-y-1">
          <p className="text-xs font-black text-blue-600">Research Inbox</p>
          <h1 className="text-xl font-black tracking-tight text-slate-950 md:text-2xl">ナレッジ確定のための質問</h1>
          <p className="text-xs font-bold text-slate-500">
            BigQuery上のKPI候補・注目指標候補・シグナル候補のうち、まだ確定していない項目を埋めるための質問です。回答すると該当レコードの確度(confidence)が更新されます。
          </p>
        </header>

        <section className="mt-4 flex flex-wrap gap-2">
          {ROLES.map((option) => {
            const active = option.value === role;
            return (
              <button
                key={option.value}
                type="button"
                onClick={() => setRole(option.value)}
                className={`rounded-full px-3 py-1 text-xs font-black transition ${
                  active ? "bg-blue-600 text-white" : "bg-slate-100 text-slate-600"
                }`}
              >
                {option.label}
              </button>
            );
          })}
        </section>

        <section className="mt-3 space-y-3">
          {data.items.length === 0 ? (
            <Card className="rounded-lg p-4 text-xs font-bold text-slate-500">
              今は{ROLES.find((option) => option.value === role)?.label}宛の追加質問はありません。
            </Card>
          ) : (
            data.items.map((item) => {
              const draft = drafts[item.assignment_id] ?? "";
              return (
                <Card key={item.assignment_id} className="space-y-3 rounded-lg">
                  <div className="flex items-center justify-between gap-2 text-[11px] font-black text-slate-500">
                    <span>{item.question_category ?? "観測"}</span>
                    <span>{item.created_at.slice(0, 16)}</span>
                  </div>
                  {item.target_candidate_name ? (
                    <p className="text-[11px] font-black text-teal-700">
                      対象: {item.target_candidate_name}
                    </p>
                  ) : null}
                  <p className="text-sm font-black leading-snug text-slate-950">{item.question_text ?? "(質問テキスト未取得)"}</p>
                  {item.reason ? <p className="text-[11px] font-bold text-slate-500">理由: {item.reason}</p> : null}
                  {item.expected_answer_format ? (
                    <p className="text-[11px] font-bold text-slate-500">回答形式: {item.expected_answer_format}</p>
                  ) : null}
                  <textarea
                    className="min-h-20 w-full resize-y rounded-md border border-slate-200 bg-white px-3 py-2 text-sm font-semibold outline-none focus:border-blue-500"
                    value={draft}
                    onChange={(event) =>
                      setDrafts((prev) => ({ ...prev, [item.assignment_id]: event.target.value }))
                    }
                    placeholder="観測した内容を短く"
                  />
                  <div className="flex justify-end">
                    <button
                      type="button"
                      disabled={!draft.trim() || submit.isPending}
                      className="rounded-full bg-teal-600 px-4 py-2 text-sm font-black text-white disabled:bg-slate-300"
                      onClick={() =>
                        submit.mutate({
                          assignment_id: item.assignment_id,
                          respondent_role: role,
                          answer_text: draft.trim(),
                          answer_payload: { question_category: item.question_category },
                        })
                      }
                    >
                      回答する
                    </button>
                  </div>
                </Card>
              );
            })
          )}
        </section>

        {submit.isSuccess ? (
          <div className="mt-3 rounded-lg bg-teal-50 px-3 py-2 text-xs font-black text-teal-700">
            回答を記録しました。対象レコードの確度(confidence)が更新されます。
          </div>
        ) : null}
        {submit.isError ? (
          <div className="mt-3 rounded-lg bg-rose-50 px-3 py-2 text-xs font-black text-rose-700">
            回答の送信に失敗しました。
          </div>
        ) : null}
      </div>
      <BottomNav active="research" />
    </PhoneFrame>
  );
};
