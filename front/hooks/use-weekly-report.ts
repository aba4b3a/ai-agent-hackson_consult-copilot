import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { generateWeeklyReport, getWeeklyReport } from "@/services/discovery-service";

export function useWeeklyReport(workspaceId: string) {
  return useQuery({
    queryKey: ["weekly-report", workspaceId],
    queryFn: () => getWeeklyReport(workspaceId),
    enabled: Boolean(workspaceId),
  });
}

export function useGenerateWeeklyReport(workspaceId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => generateWeeklyReport(workspaceId),
    onSuccess: (report) => {
      queryClient.setQueryData(["weekly-report", workspaceId], report);
    },
  });
}
