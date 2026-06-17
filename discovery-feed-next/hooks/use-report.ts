"use client";

import { useQuery } from "@tanstack/react-query";
import { getReportData } from "@/services/report-service";

export const useReport = () => {
  return useQuery({
    queryKey: ["report-chat"],
    queryFn: getReportData,
  });
};
