"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  authSessionStorageKey,
  consultantCompanies,
  type AuthSession,
  type CompanyOption,
} from "@/lib/auth-session";
import { listCompanies } from "@/services/company-service";

const toCompanyOption = (record: { company_id: string; company_name: string; company_size_segment: string | null }): CompanyOption => ({
  code: record.company_id,
  name: record.company_name,
  segment: record.company_size_segment ?? "登録企業",
});

type RegisterCompanyResult = { ok: true } | { ok: false; error: string };

type AuthContextValue = {
  session: AuthSession | null;
  isReady: boolean;
  companies: CompanyOption[];
  activeCompany: CompanyOption;
  signIn: (input: Pick<AuthSession, "consultantName" | "email" | "companyCode">) => void;
  signOut: () => void;
  switchCompany: (companyCode: string) => void;
  registerCompany: (input: CompanyOption, options?: { switchTo?: boolean }) => RegisterCompanyResult;
  removeCompany: (companyCode: string) => RegisterCompanyResult;
  isCustomCompany: (companyCode: string) => boolean;
};

const fallbackCompany = consultantCompanies[0];

const AuthContext = createContext<AuthContextValue | null>(null);

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [session, setSession] = useState<AuthSession | null>(null);
  const [isReady, setIsReady] = useState(false);
  // Companies just registered in this tab, shown immediately while the
  // POST /companies write (fired separately by useProvisionCompany) is
  // still in flight — reconciled away once the companies query below
  // refetches and the real backend row appears in its place.
  const [pendingCompanies, setPendingCompanies] = useState<CompanyOption[]>([]);

  const queryClient = useQueryClient();
  const companiesQuery = useQuery({
    queryKey: ["companies"],
    queryFn: async () => (await listCompanies()).map(toCompanyOption),
  });

  const companies = useMemo(() => {
    const backendCompanies = companiesQuery.data ?? [];
    const knownCodes = new Set([...consultantCompanies, ...backendCompanies].map((c) => c.code));
    const stillPending = pendingCompanies.filter((c) => !knownCodes.has(c.code));
    return [...consultantCompanies, ...backendCompanies, ...stillPending];
  }, [companiesQuery.data, pendingCompanies]);

  useEffect(() => {
    // localStorage is only readable client-side; this app is a static export
    // (no per-request SSR), so reading it in an effect (post-mount, post-hydration)
    // rather than a lazy useState initializer avoids a hydration mismatch.
    const storedSession = window.localStorage.getItem(authSessionStorageKey);

    if (storedSession) {
      try {
        const parsed = JSON.parse(storedSession) as AuthSession;
        // The companies list (backend-sourced) hasn't necessarily loaded yet
        // at this point, so the stored company code is trusted as-is here;
        // activeCompany below falls back to the default demo company once
        // the list resolves if it turns out not to exist anymore.
        // eslint-disable-next-line react-hooks/set-state-in-effect
        setSession({
          consultantName: parsed.consultantName?.trim() || "Consultant",
          email: parsed.email?.trim() || "",
          companyCode: parsed.companyCode || fallbackCompany.code,
        });
      } catch {
        window.localStorage.removeItem(authSessionStorageKey);
      }
    }

    setIsReady(true);
  }, []);

  const persistSession = useCallback((nextSession: AuthSession | null) => {
    setSession(nextSession);

    if (nextSession) {
      window.localStorage.setItem(authSessionStorageKey, JSON.stringify(nextSession));
      return;
    }

    window.localStorage.removeItem(authSessionStorageKey);
  }, []);

  const signIn = useCallback(
    (input: Pick<AuthSession, "consultantName" | "email" | "companyCode">) => {
      const companyExists = companies.some((company) => company.code === input.companyCode);
      persistSession({
        consultantName: input.consultantName.trim() || "Consultant",
        email: input.email.trim(),
        companyCode: companyExists ? input.companyCode : fallbackCompany.code,
      });
    },
    [companies, persistSession],
  );

  const signOut = useCallback(() => {
    persistSession(null);
  }, [persistSession]);

  const switchCompany = useCallback(
    (companyCode: string) => {
      if (!session) return;
      const companyExists = companies.some((company) => company.code === companyCode);
      if (!companyExists) return;

      persistSession({ ...session, companyCode });
    },
    [companies, persistSession, session],
  );

  const registerCompany = useCallback(
    (input: CompanyOption, options?: { switchTo?: boolean }): RegisterCompanyResult => {
      const code = input.code.trim().toUpperCase();
      const name = input.name.trim();

      if (!code) return { ok: false, error: "企業コードを入力してください。" };
      if (!name) return { ok: false, error: "企業名を入力してください。" };
      if (companies.some((company) => company.code === code)) {
        return { ok: false, error: "この企業コードは既に登録されています。" };
      }

      const nextCompany: CompanyOption = { code, name, segment: input.segment.trim() || "新規登録企業" };
      setPendingCompanies((prev) => [...prev, nextCompany]);

      if (options?.switchTo !== false && session) {
        persistSession({ ...session, companyCode: nextCompany.code });
      }

      return { ok: true };
    },
    [companies, persistSession, session],
  );

  const isCustomCompany = useCallback(
    (companyCode: string) => !consultantCompanies.some((company) => company.code === companyCode),
    [],
  );

  const removeCompany = useCallback(
    (companyCode: string): RegisterCompanyResult => {
      if (!isCustomCompany(companyCode)) {
        return { ok: false, error: "この企業は削除できません。" };
      }

      // The backend row is already gone by the time this is called (see
      // CompanySwitcher's handleDeleteCompany) — just drop any optimistic
      // pending entry and refetch so the real (now-shorter) list replaces it.
      setPendingCompanies((prev) => prev.filter((company) => company.code !== companyCode));
      void queryClient.invalidateQueries({ queryKey: ["companies"] });

      if (session?.companyCode === companyCode) {
        const remaining = companies.filter((company) => company.code !== companyCode);
        const nextActive = remaining[0] ?? fallbackCompany;
        persistSession({ ...session, companyCode: nextActive.code });
      }

      return { ok: true };
    },
    [companies, isCustomCompany, persistSession, queryClient, session],
  );

  const activeCompany = useMemo(() => {
    return companies.find((company) => company.code === session?.companyCode) ?? fallbackCompany;
  }, [companies, session?.companyCode]);

  const value = useMemo(
    () => ({
      session,
      isReady,
      companies,
      activeCompany,
      signIn,
      signOut,
      switchCompany,
      registerCompany,
      removeCompany,
      isCustomCompany,
    }),
    [
      session,
      isReady,
      companies,
      activeCompany,
      signIn,
      signOut,
      switchCompany,
      registerCompany,
      removeCompany,
      isCustomCompany,
    ],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }

  return context;
};
