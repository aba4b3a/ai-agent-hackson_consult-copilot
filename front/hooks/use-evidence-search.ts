import { useQuery } from "@tanstack/react-query";

import { searchEvidence } from "@/services/discovery-service";

export function useEvidenceSearch(workspaceId: string, query: string) {
  return useQuery({
    queryKey: ["evidence", workspaceId, query],
    queryFn: () => searchEvidence(workspaceId, query),
    enabled: Boolean(workspaceId),
  });
}
