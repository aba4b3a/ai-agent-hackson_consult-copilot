"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";
import { CompanySwitcher } from "@/components/feature/auth/CompanySwitcher";
import { useAuth } from "@/components/feature/auth/AuthProvider";

export const AppShell = ({ children }: { children: React.ReactNode }) => {
  const pathname = usePathname();
  const router = useRouter();
  const { isReady, session } = useAuth();
  const isSignInPage = pathname === "/signin";

  useEffect(() => {
    if (isReady && !session && !isSignInPage) {
      router.replace("/signin");
    }
  }, [isReady, isSignInPage, router, session]);

  if (!isReady) {
    return <div className="grid min-h-screen place-items-center text-sm font-bold text-slate-500">Loading...</div>;
  }

  if (!session && !isSignInPage) {
    return <div className="grid min-h-screen place-items-center text-sm font-bold text-slate-500">Redirecting...</div>;
  }

  return (
    <>
      {!isSignInPage ? <CompanySwitcher /> : null}
      {children}
    </>
  );
};
