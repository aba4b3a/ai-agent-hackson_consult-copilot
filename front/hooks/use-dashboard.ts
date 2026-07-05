"use client";

import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@/components/feature/auth/AuthProvider";
import { getDashboardData } from "@/services/dashboard-service";

export const useDashboard = () => {
  const { activeCompany } = useAuth();

  return useQuery({
    queryKey: ["dashboard", activeCompany.code],
    queryFn: () => getDashboardData(activeCompany.code),
    staleTime: 60_000,
  });
};
