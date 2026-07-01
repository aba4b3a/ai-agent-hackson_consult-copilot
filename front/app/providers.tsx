"use client";

import type { ReactNode } from "react";
import { QueryClientProvider } from "@tanstack/react-query";

import { queryClient } from "@/lib/react-query";

/** Client-side context providers shared across the app (TanStack Query). */
export function Providers({ children }: { children: ReactNode }) {
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}
