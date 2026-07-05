"use client";

import { FormEvent, useMemo, useState } from "react";
import { BottomNav } from "@/components/feature/discovery/BottomNav";
import { Card } from "@/components/ui/Card";
import { LoadingState } from "@/components/ui/LoadingState";
import { PhoneFrame } from "@/components/ui/PhoneFrame";
import { useInitialSurvey, useInitialSurveyStatus, useSubmitInitialSurvey } from "@/hooks/use-intake";
import type { InitialSurveyStatus, SurveyAnswerPayload, SurveyQuestion, SurveyTemplate } from "@/services/intake-service";

type AnswerValue = string | string[];
type ChatMessage = { role: "assistant" | "user"; text: string };

const categoryLabels: Record<string, string> = {
  business_structure: "事業構造",
  customer_value: "顧客・提供価値",
  competition: "競合",
  external_environment: "外部環境",
  operation: "業務・現場",
  current_kpi: "KPI",
  hypothesis: "違和感・仮説",
};

const serializeAnswer = (value: AnswerValue | undefined) => {
  if (Array.isArray(value)) return value.join(", ");
  return value ?? "";
};

const buildFollowupPrompt = (question: SurveyQuestion) => {
  if (question.answer_type === "numeric") {
    return `${question.short_label}について、数値の集計期間や単位も分かれば教えてください。`;
  }
  if (question.question_category === "competition") {
    return "競合名、比較された観点、最終的な購買結果が分かると分析しやすいです。";
  }
  if (question.question_category === "current_kpi") {
    return "その数値を誰が、どの頻度で、どの判断に使っているかも分かるとKPI候補にしやすいです。";
  }
  return "具体例、頻度、関係する商品・顧客層が分かれば追加で教えてください。";
};

const QuestionInput = ({
  question,
  value,
  onChange,
}: {
  question: SurveyQuestion;
  value: AnswerValue | undefined;
  onChange: (value: AnswerValue) => void;
}) => {
  const baseInput =
    "w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-900 outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100";

  if (question.answer_type === "single_choice") {
    return (
      <div className="grid gap-2 sm:grid-cols-2">
        {question.choices.map((choice) => {
          const checked = value === choice.value;
          return (
            <label
              key={choice.value}
              className={`flex min-h-12 cursor-pointer items-center gap-2 rounded-lg border px-3 py-2 text-sm font-bold transition ${
                checked ? "border-blue-500 bg-blue-50 text-blue-700" : "border-slate-200 bg-white text-slate-700"
              }`}
            >
              <input className="sr-only" type="radio" checked={checked} onChange={() => onChange(choice.value)} />
              <span className={`grid h-5 w-5 place-items-center rounded-full border ${checked ? "border-blue-600 bg-blue-600 text-white" : "border-slate-300"}`}>
                {checked ? "✓" : null}
              </span>
              <span>{choice.label}</span>
            </label>
          );
        })}
      </div>
    );
  }

  if (question.answer_type === "multiple_choice") {
    const selected = Array.isArray(value) ? value : [];
    return (
      <div className="grid gap-2 sm:grid-cols-2">
        {question.choices.map((choice) => {
          const checked = selected.includes(choice.value);
          return (
            <label
              key={choice.value}
              className={`flex min-h-12 cursor-pointer items-center gap-2 rounded-lg border px-3 py-2 text-sm font-bold transition ${
                checked ? "border-teal-500 bg-teal-50 text-teal-700" : "border-slate-200 bg-white text-slate-700"
              }`}
            >
              <input
                className="sr-only"
                type="checkbox"
                checked={checked}
                onChange={() => {
                  onChange(checked ? selected.filter((item) => item !== choice.value) : [...selected, choice.value]);
                }}
              />
              <span className={`grid h-5 w-5 place-items-center rounded border ${checked ? "border-teal-600 bg-teal-600 text-white" : "border-slate-300"}`}>
                {checked ? "✓" : null}
              </span>
              <span>{choice.label}</span>
            </label>
          );
        })}
      </div>
    );
  }

  if (question.answer_type === "numeric" || question.answer_type === "rating") {
    return (
      <div className="flex items-center gap-2">
        <input
          className={baseInput}
          min={question.validation.min_value ?? undefined}
          max={question.validation.max_value ?? undefined}
          step={question.validation.step ?? 1}
          type="number"
          value={typeof value === "string" ? value : ""}
          onChange={(event) => onChange(event.target.value)}
          placeholder={question.placeholder ?? undefined}
        />
        {question.validation.unit ? <span className="shrink-0 text-xs font-black text-slate-500">{question.validation.unit}</span> : null}
      </div>
    );
  }

  if (question.answer_type === "date") {
    return <input className={baseInput} type="date" value={typeof value === "string" ? value : ""} onChange={(event) => onChange(event.target.value)} />;
  }

  if (question.answer_type === "long_text" || question.answer_type === "json") {
    return (
      <textarea
        className={`${baseInput} min-h-28 resize-y leading-relaxed`}
        maxLength={question.validation.max_length ?? undefined}
        minLength={question.validation.min_length ?? undefined}
        value={typeof value === "string" ? value : ""}
        onChange={(event) => onChange(event.target.value)}
        placeholder={question.placeholder ?? undefined}
      />
    );
  }

  return (
    <input
      className={baseInput}
      maxLength={question.validation.max_length ?? undefined}
      minLength={question.validation.min_length ?? undefined}
      type="text"
      value={typeof value === "string" ? value : ""}
      onChange={(event) => onChange(event.target.value)}
      placeholder={question.placeholder ?? undefined}
    />
  );
};

const resolveAnswerDisplay = (question: SurveyQuestion, rawAnswer: string) => {
  if (question.answer_type === "single_choice" || question.answer_type === "multiple_choice") {
    const values = rawAnswer.split(",").map((value) => value.trim()).filter(Boolean);
    const labels = values.map((value) => question.choices.find((choice) => choice.value === value)?.label ?? value);
    return labels.join(" / ");
  }
  return rawAnswer;
};

const AnsweredSurveySummary = ({
  template,
  status,
  onEdit,
}: {
  template: SurveyTemplate;
  status: InitialSurveyStatus;
  onEdit: () => void;
}) => {
  const answersByQuestionId = new Map(status.answers.map((answer) => [answer.question_id, answer]));

  return (
    <div className="px-5 pb-24 pt-5 md:px-7 md:pb-8 md:pt-8">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-xs font-black text-teal-600">Initial Intake ・ 回答済み</p>
          <h1 className="mt-1 text-xl font-black tracking-tight text-slate-950 md:text-2xl">{template.title}</h1>
          <p className="mt-1 max-w-2xl text-xs font-bold leading-relaxed text-slate-500 md:text-sm">{template.description}</p>
        </div>
        <button
          className="inline-flex items-center gap-2 rounded-full bg-blue-600 px-4 py-2 text-sm font-black text-white shadow-[0_14px_30px_rgba(37,99,235,0.22)]"
          type="button"
          onClick={onEdit}
        >
          回答を編集する
        </button>
      </header>

      <div className="mt-4 rounded-lg bg-teal-50 px-4 py-3 text-sm font-black text-teal-700">
        {status.answered_count} / {status.total_count} 問に回答済みです。
      </div>

      <div className="mt-5 space-y-3">
        {template.questions.map((question) => {
          const answer = answersByQuestionId.get(question.question_id);
          return (
            <Card key={question.question_id} className="rounded-lg">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <span className="rounded-full bg-slate-100 px-3 py-1 text-[11px] font-black text-slate-600">
                  {categoryLabels[question.question_category] ?? question.question_category}
                </span>
                {answer ? (
                  <span className="text-[11px] font-black text-slate-400">{answer.respondent_role}</span>
                ) : (
                  <span className="rounded-full bg-amber-50 px-3 py-1 text-[11px] font-black text-amber-600">未回答</span>
                )}
              </div>
              <p className="mt-3 text-sm font-black leading-snug text-slate-950">{question.question_text}</p>
              <p className="mt-2 text-sm font-semibold leading-relaxed text-slate-600">
                {answer ? resolveAnswerDisplay(question, answer.raw_answer) : "-"}
              </p>
            </Card>
          );
        })}
      </div>
    </div>
  );
};

const FollowupChat = ({
  question,
  messages,
  onClose,
  onSend,
}: {
  question: SurveyQuestion;
  messages: ChatMessage[];
  onClose: () => void;
  onSend: (text: string) => void;
}) => {
  const [text, setText] = useState("");

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/35 px-4 py-6 backdrop-blur-sm">
      <div className="mx-auto flex h-full max-h-[680px] w-full max-w-lg flex-col rounded-lg bg-white shadow-2xl">
        <header className="flex items-center justify-between border-b border-slate-100 px-4 py-3">
          <div>
            <p className="text-xs font-black text-blue-600">追加質問</p>
            <p className="text-sm font-black text-slate-950">{question.short_label}</p>
          </div>
          <button className="grid h-9 w-9 place-items-center rounded-full bg-slate-100 text-slate-600" type="button" onClick={onClose} aria-label="閉じる">
            ×
          </button>
        </header>
        <div className="flex-1 space-y-3 overflow-y-auto px-4 py-4">
          {messages.map((message, index) => (
            <div key={`${message.role}-${index}`} className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}>
              <div className={`max-w-[82%] rounded-lg px-3 py-2 text-sm font-semibold leading-relaxed ${message.role === "user" ? "bg-blue-600 text-white" : "bg-slate-100 text-slate-700"}`}>
                {message.text}
              </div>
            </div>
          ))}
        </div>
        <form
          className="flex gap-2 border-t border-slate-100 p-3"
          onSubmit={(event) => {
            event.preventDefault();
            const trimmed = text.trim();
            if (!trimmed) return;
            onSend(trimmed);
            setText("");
          }}
        >
          <input
            className="min-w-0 flex-1 rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
            value={text}
            onChange={(event) => setText(event.target.value)}
            placeholder="補足を入力"
          />
          <button className="grid h-10 w-10 place-items-center rounded-full bg-blue-600 text-white" type="submit" aria-label="送信">
            →
          </button>
        </form>
      </div>
    </div>
  );
};

export const InitialSurveyForm = () => {
  const { data, isLoading, isError } = useInitialSurvey();
  const { data: status, isLoading: isStatusLoading } = useInitialSurveyStatus();
  const submitSurvey = useSubmitInitialSurvey();
  const [step, setStep] = useState(0);
  const [respondentRole, setRespondentRole] = useState("owner");
  const [answers, setAnswers] = useState<Record<string, AnswerValue>>({});
  const [chatQuestionId, setChatQuestionId] = useState<string | null>(null);
  const [chatMessages, setChatMessages] = useState<Record<string, ChatMessage[]>>({});
  const [isEditing, setIsEditing] = useState(false);

  const question = data?.questions[step];
  const chatQuestion = data?.questions.find((item) => item.question_id === chatQuestionId);
  const completedCount = useMemo(() => {
    if (!data) return 0;
    return data.questions.filter((item) => serializeAnswer(answers[item.question_id]).trim().length > 0).length;
  }, [answers, data]);

  if (isLoading || isStatusLoading) return <LoadingState message="Loading..." active="intake" />;
  if (isError || !data || !question) return <LoadingState message="質問定義を取得できませんでした。" isError active="intake" />;

  if (status?.answered && !isEditing) {
    return (
      <PhoneFrame>
        <AnsweredSurveySummary template={data} status={status} onEdit={() => setIsEditing(true)} />
        <BottomNav active="intake" />
      </PhoneFrame>
    );
  }

  const currentAnswer = answers[question.question_id];
  const isRequired = question.validation.required;
  const isAnswered = serializeAnswer(currentAnswer).trim().length > 0;
  const canGoNext = !isRequired || isAnswered;
  const progress = Math.round(((step + 1) / data.questions.length) * 100);

  const openChat = (target: SurveyQuestion) => {
    setChatQuestionId(target.question_id);
    setChatMessages((prev) => ({
      ...prev,
      [target.question_id]: prev[target.question_id] ?? [{ role: "assistant", text: buildFollowupPrompt(target) }],
    }));
  };

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    const payloadAnswers = data.questions.reduce<SurveyAnswerPayload[]>((acc, item) => {
        const value = answers[item.question_id];
        const rawAnswer = serializeAnswer(value).trim();
        if (!rawAnswer) return acc;
        const numericValue = item.answer_type === "numeric" || item.answer_type === "rating" ? Number(rawAnswer) : null;
        acc.push({
          question_id: item.question_id,
          question_text: item.question_text,
          answer_type: item.answer_type,
          respondent_role: respondentRole,
          raw_answer: rawAnswer,
          numeric_value: Number.isFinite(numericValue) ? numericValue : null,
          answer_json: {
            question_category: item.question_category,
            selected_values: Array.isArray(value) ? value : undefined,
            chat_messages: chatMessages[item.question_id] ?? [],
          },
        });
        return acc;
      }, []);

    submitSurvey.mutate({
      respondent_role: respondentRole,
      answers: payloadAnswers,
      chat_transcript: Object.values(chatMessages).flat(),
    });
  };

  return (
    <PhoneFrame>
      <form className="px-5 pb-24 pt-5 md:px-7 md:pb-8 md:pt-8" onSubmit={handleSubmit}>
        <header className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-xs font-black text-blue-600">Initial Intake</p>
            <h1 className="mt-1 text-xl font-black tracking-tight text-slate-950 md:text-2xl">{data.title}</h1>
            <p className="mt-1 max-w-2xl text-xs font-bold leading-relaxed text-slate-500 md:text-sm">{data.description}</p>
          </div>
          <label className="flex items-center gap-2 rounded-full bg-white px-3 py-2 shadow-[0_10px_24px_rgba(15,23,42,0.04)]">
            <span className="text-xs font-black text-slate-500">回答者</span>
            <select className="bg-transparent text-sm font-black text-slate-900 outline-none" value={respondentRole} onChange={(event) => setRespondentRole(event.target.value)}>
              <option value="owner">経営者</option>
              <option value="manager">管理者</option>
              <option value="sales">営業</option>
              <option value="staff">現場</option>
            </select>
          </label>
        </header>

        <section className="mt-5">
          <div className="flex items-center justify-between text-xs font-black text-slate-500">
            <span>
              {step + 1} / {data.questions.length}
            </span>
            <span>{completedCount} answered</span>
          </div>
          <div className="mt-2 h-2 overflow-hidden rounded-full bg-slate-200">
            <div className="h-full rounded-full bg-blue-600 transition-all" style={{ width: `${progress}%` }} />
          </div>
        </section>

        <Card className="mt-5 rounded-lg">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <span className="rounded-full bg-slate-100 px-3 py-1 text-[11px] font-black text-slate-600">
                {categoryLabels[question.question_category] ?? question.question_category}
              </span>
              <h2 className="mt-4 text-lg font-black leading-snug text-slate-950 md:text-xl">{question.question_text}</h2>
              {question.help_text ? <p className="mt-2 text-sm font-semibold leading-relaxed text-slate-500">{question.help_text}</p> : null}
            </div>
            {question.validation.required ? <span className="rounded-full bg-rose-50 px-3 py-1 text-[11px] font-black text-rose-600">必須</span> : null}
          </div>

          <div className="mt-5">
            <QuestionInput question={question} value={currentAnswer} onChange={(value) => setAnswers((prev) => ({ ...prev, [question.question_id]: value }))} />
          </div>

          <div className="mt-4 flex flex-wrap items-center justify-between gap-2">
            <button
              className="inline-flex items-center gap-2 rounded-full bg-slate-100 px-4 py-2 text-sm font-black text-slate-600 transition hover:bg-slate-200"
              type="button"
              onClick={() => openChat(question)}
            >
              <span aria-hidden="true">?</span>
              AIに補足する
            </button>
            <p className="text-xs font-bold text-slate-400">{question.purpose}</p>
          </div>
        </Card>

        <div className="mt-5 flex items-center justify-between gap-3">
          <button
            className="inline-flex items-center gap-2 rounded-full bg-white px-4 py-3 text-sm font-black text-slate-600 shadow-[0_10px_24px_rgba(15,23,42,0.04)] disabled:opacity-40"
            type="button"
            disabled={step === 0}
            onClick={() => setStep((value) => Math.max(value - 1, 0))}
          >
            <span aria-hidden="true">←</span>
            前へ
          </button>
          {step < data.questions.length - 1 ? (
            <button
              className="inline-flex items-center gap-2 rounded-full bg-blue-600 px-5 py-3 text-sm font-black text-white shadow-[0_14px_30px_rgba(37,99,235,0.22)] disabled:bg-slate-300 disabled:shadow-none"
              type="button"
              disabled={!canGoNext}
              onClick={() => setStep((value) => Math.min(value + 1, data.questions.length - 1))}
            >
              次へ
              <span aria-hidden="true">→</span>
            </button>
          ) : (
            <button
              className="inline-flex items-center gap-2 rounded-full bg-teal-600 px-5 py-3 text-sm font-black text-white shadow-[0_14px_30px_rgba(13,148,136,0.22)] disabled:bg-slate-300 disabled:shadow-none"
              type="submit"
              disabled={submitSurvey.isPending || completedCount === 0}
            >
              <span aria-hidden="true">→</span>
              送信
            </button>
          )}
        </div>

        {submitSurvey.isSuccess ? (
          <div className="mt-4 rounded-lg bg-teal-50 px-4 py-3 text-sm font-black text-teal-700">送信しました。回答はStorageに保存され、Knowledge処理に渡せる形式になっています。</div>
        ) : null}
        {submitSurvey.isError ? (
          <div className="mt-4 rounded-lg bg-rose-50 px-4 py-3 text-sm font-black text-rose-700">送信に失敗しました。</div>
        ) : null}
      </form>

      {chatQuestion ? (
        <FollowupChat
          question={chatQuestion}
          messages={chatMessages[chatQuestion.question_id] ?? []}
          onClose={() => setChatQuestionId(null)}
          onSend={(text) => {
            setChatMessages((prev) => ({
              ...prev,
              [chatQuestion.question_id]: [...(prev[chatQuestion.question_id] ?? []), { role: "user", text }],
            }));
          }}
        />
      ) : null}
      <BottomNav active="intake" />
    </PhoneFrame>
  );
};
