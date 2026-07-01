import { useMutation, useQueryClient } from "@tanstack/react-query";

import { submitReport } from "@/services/discovery-service";

/** Invalidate the knowledge views a new source feeds into, so the consultant
 *  dashboard reflects the freshly extracted observations/signals. */
function useInvalidateKnowledge() {
  const queryClient = useQueryClient();
  return () => {
    for (const key of ["dashboard", "evidence", "graph-slice", "weekly-report"]) {
      queryClient.invalidateQueries({ queryKey: [key] });
    }
  };
}

export function useSubmitReport() {
  const invalidate = useInvalidateKnowledge();
  return useMutation({
    mutationFn: submitReport,
    onSuccess: invalidate,
  });
}
