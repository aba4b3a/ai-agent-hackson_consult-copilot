import { useMutation } from "@tanstack/react-query";

import { getFollowups } from "@/services/discovery-service";

export function useFollowups(workspaceId: string) {
  return useMutation({
    mutationFn: (answers: string[]) => getFollowups(workspaceId, answers),
  });
}
