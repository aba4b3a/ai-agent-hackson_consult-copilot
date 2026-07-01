import { useMutation } from "@tanstack/react-query";

import { createReportForm } from "@/services/discovery-service";

export function useCreateReportForm() {
  return useMutation({
    mutationFn: createReportForm,
  });
}
