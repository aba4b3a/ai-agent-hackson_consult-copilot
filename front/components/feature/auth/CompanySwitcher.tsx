"use client";

import { useRouter } from "next/navigation";
import { useAuth } from "@/components/feature/auth/AuthProvider";
import { consultantCompanies } from "@/lib/auth-session";

export const CompanySwitcher = () => {
  const router = useRouter();
  const { activeCompany, session, signOut, switchCompany } = useAuth();

  if (!session) return null;

  const handleSignOut = () => {
    signOut();
    router.push("/signin");
  };

  return (
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
          {consultantCompanies.map((company) => (
            <option key={company.code} value={company.code}>
              {company.code} / {company.name}
            </option>
          ))}
        </select>
      </div>

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
  );
};
