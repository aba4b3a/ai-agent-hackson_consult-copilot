import { useQuery } from "@tanstack/react-query";

import { getReportForm } from "@/services/discovery-service";

export function useReportForm(formId: string) {
  return useQuery({
    queryKey: ["report-form", formId],
    queryFn: () => getReportForm(formId),
    enabled: Boolean(formId),
  });
}
