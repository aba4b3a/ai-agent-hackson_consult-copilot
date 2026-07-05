import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@/components/feature/auth/AuthProvider";
import { getReportCopilotData } from "@/services/report-copilot-service";

export const useReportCopilot = () => {
  const { activeCompany } = useAuth();

  return useQuery({
    queryKey: ["report-copilot", activeCompany.code],
    queryFn: () => getReportCopilotData(activeCompany.code),
  });
};
