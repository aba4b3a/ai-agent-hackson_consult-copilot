"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import {
  authSessionStorageKey,
  consultantCompanies,
  loadCustomCompanies,
  saveCustomCompanies,
  type AuthSession,
  type CompanyOption,
} from "@/lib/auth-session";

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
  const [customCompanies, setCustomCompanies] = useState<CompanyOption[]>([]);

  const companies = useMemo(() => [...consultantCompanies, ...customCompanies], [customCompanies]);

  useEffect(() => {
    const loadedCustomCompanies = loadCustomCompanies();
    // localStorage is only readable client-side; this app is a static export
    // (no per-request SSR), so reading it in an effect (post-mount, post-hydration)
    // rather than a lazy useState initializer avoids a hydration mismatch.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setCustomCompanies(loadedCustomCompanies);

    const storedSession = window.localStorage.getItem(authSessionStorageKey);

    if (storedSession) {
      try {
        const parsed = JSON.parse(storedSession) as AuthSession;
        const allCompanies = [...consultantCompanies, ...loadedCustomCompanies];
        const companyExists = allCompanies.some((company) => company.code === parsed.companyCode);
        setSession({
          consultantName: parsed.consultantName?.trim() || "Consultant",
          email: parsed.email?.trim() || "",
          companyCode: companyExists ? parsed.companyCode : fallbackCompany.code,
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
      const nextCustomCompanies = [...customCompanies, nextCompany];
      setCustomCompanies(nextCustomCompanies);
      saveCustomCompanies(nextCustomCompanies);

      if (options?.switchTo !== false && session) {
        persistSession({ ...session, companyCode: nextCompany.code });
      }

      return { ok: true };
    },
    [companies, customCompanies, persistSession, session],
  );

  const isCustomCompany = useCallback(
    (companyCode: string) => customCompanies.some((company) => company.code === companyCode),
    [customCompanies],
  );

  const removeCompany = useCallback(
    (companyCode: string): RegisterCompanyResult => {
      if (!isCustomCompany(companyCode)) {
        return { ok: false, error: "この企業は削除できません。" };
      }

      const nextCustomCompanies = customCompanies.filter((company) => company.code !== companyCode);
      setCustomCompanies(nextCustomCompanies);
      saveCustomCompanies(nextCustomCompanies);

      if (session?.companyCode === companyCode) {
        const nextActive = [...consultantCompanies, ...nextCustomCompanies][0] ?? fallbackCompany;
        persistSession({ ...session, companyCode: nextActive.code });
      }

      return { ok: true };
    },
    [customCompanies, isCustomCompany, persistSession, session],
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
