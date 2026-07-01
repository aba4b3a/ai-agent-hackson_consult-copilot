import { useQuery } from "@tanstack/react-query";

import { getGraphSlice } from "@/services/discovery-service";

export function useGraphSlice(workspaceId: string) {
  return useQuery({
    queryKey: ["graph-slice", workspaceId],
    queryFn: () => getGraphSlice(workspaceId),
    enabled: Boolean(workspaceId),
  });
}
