import { useQuery } from "@tanstack/react-query";

import { getGraphSlice, type GraphView } from "@/services/discovery-service";

export function useGraphSlice(workspaceId: string, view: GraphView) {
  return useQuery({
    queryKey: ["graph-slice", workspaceId, view],
    queryFn: () => getGraphSlice(workspaceId, view),
    enabled: Boolean(workspaceId),
  });
}
