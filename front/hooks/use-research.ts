import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { useAuth } from "@/components/feature/auth/AuthProvider";
import {
  listAssignments,
  submitFollowupAnswer,
  type AssignmentStatus,
  type FollowupAnswerSubmit,
} from "@/services/research-service";

export const useAssignments = (params: {
  targetRole?: string;
  status?: AssignmentStatus;
  origin?: string;
}) => {
  const { activeCompany } = useAuth();

  return useQuery({
    queryKey: [
      "research-assignments",
      activeCompany.code,
      params.targetRole ?? "all",
      params.status ?? "open",
      params.origin ?? "all",
    ],
    queryFn: () => listAssignments(params, activeCompany.code),
    staleTime: 15_000,
  });
};

export const useSubmitFollowupAnswer = () => {
  const qc = useQueryClient();
  const { activeCompany } = useAuth();

  return useMutation({
    mutationFn: (body: FollowupAnswerSubmit) => submitFollowupAnswer(body, activeCompany.code),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["research-assignments", activeCompany.code] }),
  });
};
