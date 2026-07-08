"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@/components/feature/auth/AuthProvider";
import { getInitialSurvey, getInitialSurveyStatus, submitInitialSurvey } from "@/services/intake-service";

export const useInitialSurvey = () => {
  const { activeCompany } = useAuth();

  return useQuery({
    queryKey: ["initial-survey", activeCompany.code],
    queryFn: () => getInitialSurvey(activeCompany.code),
  });
};

export const useInitialSurveyStatus = () => {
  const { activeCompany } = useAuth();

  return useQuery({
    queryKey: ["initial-survey-status", activeCompany.code],
    queryFn: () => getInitialSurveyStatus(activeCompany.code),
    // Wiki/BigQuery generation runs as an agent background task after
    // submit; poll until it leaves "processing" so the UI can reflect
    // completion without a manual refresh.
    refetchInterval: (query) => (query.state.data?.onboarding_status === "processing" ? 3000 : false),
  });
};

export const useSubmitInitialSurvey = () => {
  const { activeCompany } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (body: Parameters<typeof submitInitialSurvey>[0]) => submitInitialSurvey(body, activeCompany.code),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["initial-survey-status", activeCompany.code] });
    },
  });
};
