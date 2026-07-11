"use client";

import { useState } from "react";
import { Card } from "@/components/ui/Card";
import { useAssignments, useSubmitFollowupAnswer } from "@/hooks/use-research";

const ROLES = [
  { value: "owner", label: "経営者" },
  { value: "manager", label: "管理者" },
  { value: "sales", label: "営業" },
  { value: "staff", label: "現場" },
];

export const OnboardingFollowupStep = () => {
  const [role, setRole] = useState("owner");
  const { data, isLoading } = useAssignments({ origin: "onboarding", status: "open", targetRole: role });
  const submit = useSubmitFollowupAnswer();
  const [drafts, setDrafts] = useState<Record<string, string>>({});
  const [isSubmittingAll, setIsSubmittingAll] = useState(false);

  const items = data?.items ?? [];
  const answeredCount = items.filter((item) => (drafts[item.assignment_id] ?? "").trim().length > 0).length;
  const allAnswered = items.length > 0 && answeredCount === items.length;

  const handleSubmitAll = async () => {
    setIsSubmittingAll(true);
    try {
      for (const item of items) {
        const draft = (drafts[item.assignment_id] ?? "").trim();
        if (!draft) continue;
        await submit.mutateAsync({
          assignment_id: item.assignment_id,
          respondent_role: role,
          answer_text: draft,
        });
      }
    } finally {
      setIsSubmittingAll(false);
    }
  };

  return (
    <div className="px-5 pb-24 pt-5 md:px-7 md:pb-8 md:pt-8">
      <header>
        <p className="text-xs font-black text-blue-600">Initial Intake ・ 追加質問</p>
        <h1 className="mt-1 text-xl font-black tracking-tight text-slate-950 md:text-2xl">
          もう少し詳しく教えてください
        </h1>
        <p className="mt-1 max-w-2xl text-xs font-bold leading-relaxed text-slate-500 md:text-sm">
          初期の回答をもとに、AIがこの企業について深掘りしたい質問を用意しました。すべて入力して一番下の送信ボタンを押すと、Wikiが自動的に更新・確定されます。
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

      <section className="mt-4 space-y-3">
        {isLoading ? (
          <Card className="rounded-lg p-4 text-xs font-bold text-slate-500">質問を読み込み中...</Card>
        ) : items.length === 0 ? (
          <Card className="rounded-lg p-4 text-xs font-bold text-slate-500">
            {ROLES.find((option) => option.value === role)?.label}宛の追加質問はすべて回答済みです。
          </Card>
        ) : (
          items.map((item) => {
            const draft = drafts[item.assignment_id] ?? "";
            return (
              <Card key={item.assignment_id} className="space-y-3 rounded-lg">
                {item.reason ? <p className="text-[11px] font-bold text-slate-500">{item.reason}</p> : null}
                <p className="text-sm font-black leading-snug text-slate-950">
                  {item.question_text ?? "(質問テキスト未取得)"}
                </p>
                <textarea
                  className="min-h-24 w-full resize-y rounded-md border border-slate-200 bg-white px-3 py-2 text-sm font-semibold outline-none focus:border-blue-500"
                  value={draft}
                  onChange={(event) => setDrafts((prev) => ({ ...prev, [item.assignment_id]: event.target.value }))}
                  placeholder="回答を入力"
                />
              </Card>
            );
          })
        )}
      </section>

      {items.length > 0 ? (
        <div className="mt-5 flex flex-col items-end gap-2">
          <p className="text-xs font-bold text-slate-500">{answeredCount} / {items.length} 件入力済み</p>
          <button
            type="button"
            disabled={!allAnswered || isSubmittingAll}
            className="inline-flex items-center gap-2 rounded-full bg-teal-600 px-5 py-3 text-sm font-black text-white shadow-[0_14px_30px_rgba(13,148,136,0.22)] disabled:bg-slate-300 disabled:shadow-none"
            onClick={handleSubmitAll}
          >
            {isSubmittingAll ? "送信中..." : "すべて回答して送信する"}
          </button>
        </div>
      ) : null}

      {submit.isError ? (
        <div className="mt-4 rounded-lg bg-rose-50 px-4 py-3 text-sm font-black text-rose-700">
          回答の送信に失敗しました。もう一度お試しください。
        </div>
      ) : null}
    </div>
  );
};
