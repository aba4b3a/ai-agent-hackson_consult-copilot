"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/components/feature/auth/AuthProvider";
import { consultantCompanies } from "@/lib/auth-session";

const platformSignals = [
  { label: "初期ヒアリング", detail: "18問から企業モデルを作成", mark: "01" },
  { label: "KPI候補", detail: "結果指標と先行指標を分離", mark: "KPI" },
  { label: "LLM Wiki", detail: "企業別ナレッジを版管理", mark: "DB" },
];

export const SignInPage = () => {
  const router = useRouter();
  const { session, signIn } = useAuth();
  const [consultantName, setConsultantName] = useState("佐藤 里奈");
  const [email, setEmail] = useState("rina.sato@example.com");
  const [companyCode, setCompanyCode] = useState(consultantCompanies[0].code);

  useEffect(() => {
    if (session) {
      router.replace("/");
    }
  }, [router, session]);

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    signIn({ consultantName, email, companyCode });
    router.push("/");
  };

  const selectedCompany = consultantCompanies.find((company) => company.code === companyCode) ?? consultantCompanies[0];

  return (
    <main className="min-h-screen bg-slate-950 text-white">
      <div className="grid min-h-screen lg:grid-cols-[1.05fr_0.95fr]">
        <section className="flex min-h-[46vh] flex-col justify-between bg-[linear-gradient(135deg,#0f172a_0%,#14532d_48%,#0f766e_100%)] px-6 py-8 sm:px-10 lg:min-h-screen lg:px-14">
          <div className="flex items-center gap-3">
            <div className="grid h-10 w-10 place-items-center rounded-lg bg-white text-slate-950">
              <span aria-hidden="true" className="text-sm font-black">
                AI
              </span>
            </div>
            <div>
              <p className="text-sm font-black">Consult Copilot</p>
              <p className="text-xs font-semibold text-white/70">AI組織学習プラットフォーム</p>
            </div>
          </div>

          <div className="mt-14 max-w-2xl lg:mt-0">
            <p className="text-sm font-bold text-emerald-100">コンサルタント向けサインイン</p>
            <h1 className="mt-4 text-4xl font-black leading-tight tracking-normal text-white sm:text-5xl">
              企業固有のKPIと観測方針を、継続質問から育てる。
            </h1>
            <p className="mt-5 max-w-xl text-base font-medium leading-8 text-white/78">
              初期回答、Research Agentの追加質問、人間承認をつなぎ、LLM WikiとBigQueryへ反映するための作業入口です。
            </p>
          </div>

          <div className="mt-10 grid gap-3 sm:grid-cols-3 lg:mt-0">
            {platformSignals.map((signal) => {
              return (
                <div key={signal.label} className="rounded-lg border border-white/15 bg-white/10 p-4">
                  <span aria-hidden="true" className="text-xs font-black text-emerald-100">
                    {signal.mark}
                  </span>
                  <p className="mt-3 text-sm font-black">{signal.label}</p>
                  <p className="mt-1 text-xs font-semibold leading-5 text-white/70">{signal.detail}</p>
                </div>
              );
            })}
          </div>
        </section>

        <section className="flex items-center justify-center bg-slate-100 px-5 py-8 text-slate-950 sm:px-8 lg:px-12">
          <form className="w-full max-w-md rounded-lg bg-white p-6 shadow-[0_24px_70px_rgba(15,23,42,0.18)] sm:p-8" onSubmit={handleSubmit}>
            <div>
              <p className="text-xs font-black uppercase tracking-normal text-emerald-700">Secure workspace</p>
              <h2 className="mt-2 text-2xl font-black text-slate-950">サインイン</h2>
              <p className="mt-2 text-sm font-semibold leading-6 text-slate-500">
                担当企業を選ぶと、サインイン後の全画面右上に企業コードが表示されます。
              </p>
            </div>

            <div className="mt-6 space-y-4">
              <label className="block">
                <span className="text-xs font-black text-slate-600">コンサルタント名</span>
                <input
                  className="mt-2 w-full rounded-lg border border-slate-200 bg-white px-4 py-3 text-sm font-bold outline-none transition focus:border-emerald-600 focus:ring-4 focus:ring-emerald-100"
                  value={consultantName}
                  onChange={(event) => setConsultantName(event.target.value)}
                  required
                />
              </label>

              <label className="block">
                <span className="text-xs font-black text-slate-600">メールアドレス</span>
                <input
                  className="mt-2 w-full rounded-lg border border-slate-200 bg-white px-4 py-3 text-sm font-bold outline-none transition focus:border-emerald-600 focus:ring-4 focus:ring-emerald-100"
                  type="email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  required
                />
              </label>

              <label className="block">
                <span className="text-xs font-black text-slate-600">初期表示する企業</span>
                <select
                  className="mt-2 w-full rounded-lg border border-slate-200 bg-white px-4 py-3 text-sm font-black outline-none transition focus:border-emerald-600 focus:ring-4 focus:ring-emerald-100"
                  value={companyCode}
                  onChange={(event) => setCompanyCode(event.target.value)}
                >
                  {consultantCompanies.map((company) => (
                    <option key={company.code} value={company.code}>
                      {company.code} / {company.name}
                    </option>
                  ))}
                </select>
              </label>
            </div>

            <div className="mt-5 rounded-lg border border-emerald-100 bg-emerald-50 p-4">
              <p className="text-xs font-black text-emerald-900">{selectedCompany.code}</p>
              <p className="mt-1 text-sm font-black text-slate-950">{selectedCompany.name}</p>
              <p className="mt-1 text-xs font-semibold leading-5 text-slate-600">{selectedCompany.segment}</p>
            </div>

            <button
              className="mt-6 flex w-full items-center justify-center gap-2 rounded-lg bg-slate-950 px-4 py-3 text-sm font-black text-white transition hover:bg-slate-800"
              type="submit"
            >
              サインインして開始
              <span aria-hidden="true" className="text-base leading-none">
                →
              </span>
            </button>
          </form>
        </section>
      </div>
    </main>
  );
};
