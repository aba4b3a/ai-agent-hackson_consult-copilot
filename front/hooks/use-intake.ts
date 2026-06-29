"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { getInitialSurvey, submitInitialSurvey } from "@/services/intake-service";

export const useInitialSurvey = () => {
  return useQuery({
    queryKey: ["initial-survey"],
    queryFn: getInitialSurvey,
  });
};

export const useSubmitInitialSurvey = () => {
  return useMutation({
    mutationFn: submitInitialSurvey,
  });
};
