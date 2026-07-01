import { useMutation, useQueryClient } from "@tanstack/react-query";

import { submitVoice } from "@/services/discovery-service";

export function useSubmitVoice() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: submitVoice,
    onSuccess: () => {
      for (const key of ["dashboard", "evidence", "graph-slice", "weekly-report"]) {
        queryClient.invalidateQueries({ queryKey: [key] });
      }
    },
  });
}
