"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { useAuth } from "@/components/feature/auth/AuthProvider";
import { getInitialSurvey, submitInitialSurvey } from "@/services/intake-service";

export const useInitialSurvey = () => {
  const { activeCompany } = useAuth();

  return useQuery({
    queryKey: ["initial-survey", activeCompany.code],
    queryFn: () => getInitialSurvey(activeCompany.code),
  });
};

export const useSubmitInitialSurvey = () => {
  const { activeCompany } = useAuth();

  return useMutation({
    mutationFn: (body: Parameters<typeof submitInitialSurvey>[0]) => submitInitialSurvey(body, activeCompany.code),
  });
};
