import { useQuery } from "@tanstack/react-query";

import { listWorkspaces } from "@/services/discovery-service";

export function useWorkspaces() {
  return useQuery({
    queryKey: ["workspaces"],
    queryFn: listWorkspaces,
  });
}
