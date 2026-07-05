"use client";

import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@/components/feature/auth/AuthProvider";
import { getReportData } from "@/services/report-service";

export const useReport = () => {
  const { activeCompany } = useAuth();

  return useQuery({
    queryKey: ["report-chat", activeCompany.code],
    queryFn: () => getReportData(activeCompany.code),
  });
};
