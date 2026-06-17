import { useQuery } from "@tanstack/react-query";
import { getReportCopilotData } from "@/services/report-copilot-service";

export const useReportCopilot = () => {
  return useQuery({ queryKey: ["report-copilot"], queryFn: getReportCopilotData });
};
