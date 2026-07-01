import { useMutation } from "@tanstack/react-query";

import { askCopilot } from "@/services/discovery-service";

export function useCopilot(workspaceId: string) {
  return useMutation({
    mutationFn: (question: string) => askCopilot(workspaceId, question),
  });
}
