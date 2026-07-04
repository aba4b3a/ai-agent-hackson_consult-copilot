"use client";

import { QueryClientProvider } from "@tanstack/react-query";
import { AppShell } from "@/components/feature/auth/AppShell";
import { AuthProvider } from "@/components/feature/auth/AuthProvider";
import { queryClient } from "@/lib/react-query";

export const Providers = ({ children }: { children: React.ReactNode }) => {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <AppShell>{children}</AppShell>
      </AuthProvider>
    </QueryClientProvider>
  );
};
