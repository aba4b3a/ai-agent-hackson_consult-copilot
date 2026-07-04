"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { authSessionStorageKey, consultantCompanies, type AuthSession } from "@/lib/auth-session";

type AuthContextValue = {
  session: AuthSession | null;
  isReady: boolean;
  activeCompany: (typeof consultantCompanies)[number];
  signIn: (input: Pick<AuthSession, "consultantName" | "email" | "companyCode">) => void;
  signOut: () => void;
  switchCompany: (companyCode: string) => void;
};

const fallbackCompany = consultantCompanies[0];

const AuthContext = createContext<AuthContextValue | null>(null);

const normalizeSession = (session: AuthSession): AuthSession => {
  const companyExists = consultantCompanies.some((company) => company.code === session.companyCode);

  return {
    consultantName: session.consultantName.trim() || "Consultant",
    email: session.email.trim(),
    companyCode: companyExists ? session.companyCode : fallbackCompany.code,
  };
};

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [session, setSession] = useState<AuthSession | null>(null);
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    const storedSession = window.localStorage.getItem(authSessionStorageKey);

    if (storedSession) {
      try {
        setSession(normalizeSession(JSON.parse(storedSession) as AuthSession));
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
      persistSession(normalizeSession(input));
    },
    [persistSession],
  );

  const signOut = useCallback(() => {
    persistSession(null);
  }, [persistSession]);

  const switchCompany = useCallback(
    (companyCode: string) => {
      if (!session) return;
      const companyExists = consultantCompanies.some((company) => company.code === companyCode);
      if (!companyExists) return;

      persistSession({ ...session, companyCode });
    },
    [persistSession, session],
  );

  const activeCompany = useMemo(() => {
    return consultantCompanies.find((company) => company.code === session?.companyCode) ?? fallbackCompany;
  }, [session?.companyCode]);

  const value = useMemo(
    () => ({ session, isReady, activeCompany, signIn, signOut, switchCompany }),
    [activeCompany, isReady, session, signIn, signOut, switchCompany],
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
