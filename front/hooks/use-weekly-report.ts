import { useQuery } from "@tanstack/react-query";

import { getWeeklyReport } from "@/services/discovery-service";

export function useWeeklyReport(workspaceId: string) {
  return useQuery({
    queryKey: ["weekly-report", workspaceId],
    queryFn: () => getWeeklyReport(workspaceId),
    enabled: Boolean(workspaceId),
  });
}
