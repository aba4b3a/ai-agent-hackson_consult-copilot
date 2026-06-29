import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  approveApproval,
  listApprovals,
  rejectApproval,
  type ApprovalStatus,
} from "@/services/approval-service";

export const useApprovalList = (status?: ApprovalStatus) =>
  useQuery({
    queryKey: ["approvals", status ?? "all"],
    queryFn: () => listApprovals(status),
    staleTime: 15_000,
  });

export const useApproveApproval = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (params: { approvalId: string; decidedBy: string; note?: string }) =>
      approveApproval(params.approvalId, params.decidedBy, params.note),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["approvals"] }),
  });
};

export const useRejectApproval = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (params: { approvalId: string; decidedBy: string; note?: string }) =>
      rejectApproval(params.approvalId, params.decidedBy, params.note),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["approvals"] }),
  });
};
