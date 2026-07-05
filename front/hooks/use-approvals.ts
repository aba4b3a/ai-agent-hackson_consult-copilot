import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { useAuth } from "@/components/feature/auth/AuthProvider";
import {
  approveApproval,
  listApprovals,
  rejectApproval,
  type ApprovalStatus,
} from "@/services/approval-service";

export const useApprovalList = (status?: ApprovalStatus) => {
  const { activeCompany } = useAuth();

  return useQuery({
    queryKey: ["approvals", activeCompany.code, status ?? "all"],
    queryFn: () => listApprovals(status, activeCompany.code),
    staleTime: 15_000,
  });
};

export const useApproveApproval = () => {
  const qc = useQueryClient();
  const { activeCompany } = useAuth();

  return useMutation({
    mutationFn: (params: { approvalId: string; decidedBy: string; note?: string }) =>
      approveApproval(params.approvalId, params.decidedBy, params.note, activeCompany.code),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["approvals", activeCompany.code] }),
  });
};

export const useRejectApproval = () => {
  const qc = useQueryClient();
  const { activeCompany } = useAuth();

  return useMutation({
    mutationFn: (params: { approvalId: string; decidedBy: string; note?: string }) =>
      rejectApproval(params.approvalId, params.decidedBy, params.note, activeCompany.code),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["approvals", activeCompany.code] }),
  });
};
