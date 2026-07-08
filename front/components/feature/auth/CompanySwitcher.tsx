"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/components/feature/auth/AuthProvider";
import { useProvisionCompany } from "@/hooks/use-company-onboarding";
import { ApiError } from "@/lib/api-client";
import { deleteCompanyMaster } from "@/services/company-service";

const RegisterCompanyModal = ({ onClose }: { onClose: () => void }) => {
  const router = useRouter();
  const { registerCompany } = useAuth();
  const provisionCompany = useProvisionCompany();
  const [code, setCode] = useState("");
  const [name, setName] = useState("");
  const [segment, setSegment] = useState("");
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);

    const trimmedCode = code.trim().toUpperCase();
    const trimmedName = name.trim();
    const result = registerCompany({ code: trimmedCode, name: trimmedName, segment }, { switchTo: true });
    if (!result.ok) {
      setError(result.error);
      return;
    }

    onClose();
    router.push("/intake");
    provisionCompany.mutate({
      companyId: trimmedCode,
      company_name: trimmedName,
      industry_hint: segment.trim() || null,
    });
  };

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-slate-950/40 px-4 backdrop-blur-sm">
      <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-2xl">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-xs font-black text-blue-600">New Company</p>
            <h2 className="mt-1 text-lg font-black text-slate-950">新規企業を登録</h2>
            <p className="mt-1 text-xs font-semibold leading-relaxed text-slate-500">
              登録後、初期ヒアリング画面に移動します。回答は未回答の状態から体験できます。
            </p>
          </div>
          <button
            type="button"
            className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-slate-100 text-slate-600"
            onClick={onClose}
            aria-label="閉じる"
          >
            ×
          </button>
        </div>

        <form className="mt-5 space-y-3" onSubmit={handleSubmit}>
          <label className="block">
            <span className="text-xs font-black text-slate-600">企業コード</span>
            <input
              className="mt-2 w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-bold outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
              value={code}
              onChange={(event) => setCode(event.target.value)}
              placeholder="例: SMB-5001"
              required
            />
          </label>
          <label className="block">
            <span className="text-xs font-black text-slate-600">企業名</span>
            <input
              className="mt-2 w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-bold outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
              value={name}
              onChange={(event) => setName(event.target.value)}
              placeholder="例: 田中美容室"
              required
            />
          </label>
          <label className="block">
            <span className="text-xs font-black text-slate-600">業種・セグメント（任意）</span>
            <input
              className="mt-2 w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-bold outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
              value={segment}
              onChange={(event) => setSegment(event.target.value)}
              placeholder="例: 美容・サービス業"
            />
          </label>

          {error ? <p className="text-xs font-black text-rose-600">{error}</p> : null}

          <button
            className="mt-2 flex w-full items-center justify-center gap-2 rounded-full bg-blue-600 px-4 py-3 text-sm font-black text-white shadow-[0_14px_30px_rgba(37,99,235,0.22)]"
            type="submit"
          >
            登録して初期ヒアリングへ
          </button>
        </form>
      </div>
    </div>
  );
};

export const CompanySwitcher = () => {
  const router = useRouter();
  const { activeCompany, companies, session, signOut, switchCompany, removeCompany, isCustomCompany } = useAuth();
  const [isRegisterOpen, setIsRegisterOpen] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  if (!session) return null;

  const handleSignOut = () => {
    signOut();
    router.push("/signin");
  };

  const handleDeleteCompany = async () => {
    const target = activeCompany;
    if (!window.confirm(`${target.code} / ${target.name} を削除しますか？\n(BigQuery上のデータは論理削除され、一覧から非表示になります。実データは残ります。)`)) {
      return;
    }

    setDeleteError(null);
    setIsDeleting(true);
    try {
      try {
        await deleteCompanyMaster(target.code);
      } catch (error) {
        // 404 = マスタ行がそもそも存在しない(この企業登録フロー導入前に追加された企業)。
        // その場合も「一覧から消す」という意図は達成できるので、ローカル一覧からは削除する。
        if (!(error instanceof ApiError) || error.status !== 404) {
          throw error;
        }
      }
      const result = removeCompany(target.code);
      if (!result.ok) {
        setDeleteError(result.error);
      }
    } catch {
      setDeleteError("削除に失敗しました。バックエンドの起動状態を確認してください。");
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <>
      <div className="fixed right-4 top-4 z-40 flex max-w-[calc(100vw-2rem)] items-center gap-2 rounded-lg border border-slate-200 bg-white/95 px-3 py-2 text-slate-900 shadow-[0_12px_28px_rgba(15,23,42,0.12)] backdrop-blur md:right-6 xl:right-[27rem]">
        <div className="grid h-8 w-8 shrink-0 place-items-center rounded-md bg-slate-900 text-white">
          <span aria-hidden="true" className="text-xs font-black">
            Co
          </span>
        </div>

        <div className="min-w-0">
          <p className="text-[10px] font-bold leading-none text-slate-500">表示中の企業コード</p>
          <select
            aria-label="表示中の企業を切り替え"
            className="mt-1 max-w-[52vw] rounded-md border border-slate-200 bg-white px-2 py-1 text-xs font-black text-slate-950 outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100 sm:max-w-none"
            value={activeCompany.code}
            onChange={(event) => switchCompany(event.target.value)}
          >
            {companies.map((company) => (
              <option key={company.code} value={company.code}>
                {company.code} / {company.name}
              </option>
            ))}
          </select>
        </div>

        <button
          type="button"
          className="grid h-8 w-8 shrink-0 place-items-center rounded-md border border-slate-200 text-slate-500 transition hover:bg-slate-50 hover:text-slate-900"
          onClick={() => setIsRegisterOpen(true)}
          aria-label="新規企業を登録"
          title="新規企業を登録"
        >
          <span aria-hidden="true" className="text-base font-black leading-none">
            +
          </span>
        </button>

        {isCustomCompany(activeCompany.code) ? (
          <button
            type="button"
            className="h-8 shrink-0 rounded-md border border-slate-200 px-2 text-[11px] font-black text-rose-500 transition hover:bg-rose-50 hover:text-rose-700 disabled:opacity-40"
            onClick={() => void handleDeleteCompany()}
            disabled={isDeleting}
            aria-label="表示中の企業を削除"
            title="表示中の企業を削除"
          >
            削除
          </button>
        ) : null}

        <button
          type="button"
          className="grid h-8 w-8 shrink-0 place-items-center rounded-md border border-slate-200 text-slate-500 transition hover:bg-slate-50 hover:text-slate-900"
          onClick={handleSignOut}
          aria-label="サインアウト"
          title="サインアウト"
        >
          <span aria-hidden="true" className="text-base font-black leading-none">
            x
          </span>
        </button>
      </div>

      {deleteError ? (
        <div className="fixed right-4 top-16 z-40 max-w-[calc(100vw-2rem)] rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-xs font-bold text-rose-700 shadow-md md:right-6 xl:right-[27rem]">
          {deleteError}
        </div>
      ) : null}

      {isRegisterOpen ? <RegisterCompanyModal onClose={() => setIsRegisterOpen(false)} /> : null}
    </>
  );
};
