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
    // TODO: localStorage 復元は useSyncExternalStore 等への移行を検討（react-hooks v6 対応）
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

  const activeCompany = useMemo(() => {
    return companies.find((company) => company.code === session?.companyCode) ?? fallbackCompany;
  }, [companies, session?.companyCode]);

  const value = useMemo(
    () => ({ session, isReady, companies, activeCompany, signIn, signOut, switchCompany, registerCompany }),
    [session, isReady, companies, activeCompany, signIn, signOut, switchCompany, registerCompany],
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
