"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@/components/feature/auth/AuthProvider";
import {
  getInitialSurvey,
  getInitialSurveyStatus,
  retryOnboarding,
  sendIntakeAssistMessage,
  submitInitialSurvey,
} from "@/services/intake-service";

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
    // submit, and moves through processing -> awaiting_followup ->
    // finalizing -> completed; poll through all the in-progress states so
    // the UI reflects each stage (and the follow-up question list) without
    // a manual refresh.
    refetchInterval: (query) =>
      ["processing", "awaiting_followup", "finalizing"].includes(query.state.data?.onboarding_status ?? "")
        ? 3000
        : false,
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

export const useIntakeAssist = () => {
  const { activeCompany } = useAuth();

  return useMutation({
    mutationFn: (body: Parameters<typeof sendIntakeAssistMessage>[0]) =>
      sendIntakeAssistMessage(body, activeCompany.code),
  });
};

export const useRetryOnboarding = () => {
  const { activeCompany } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => retryOnboarding(activeCompany.code),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["initial-survey-status", activeCompany.code] });
    },
  });
};
