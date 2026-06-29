import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  listAssignments,
  submitFollowupAnswer,
  type AssignmentStatus,
  type FollowupAnswerSubmit,
} from "@/services/research-service";

export const useAssignments = (params: {
  targetRole?: string;
  status?: AssignmentStatus;
}) =>
  useQuery({
    queryKey: ["research-assignments", params.targetRole ?? "all", params.status ?? "open"],
    queryFn: () => listAssignments(params),
    staleTime: 15_000,
  });

export const useSubmitFollowupAnswer = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: FollowupAnswerSubmit) => submitFollowupAnswer(body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["research-assignments"] }),
  });
};
