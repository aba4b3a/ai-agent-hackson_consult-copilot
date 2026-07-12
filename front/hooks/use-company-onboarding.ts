"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  createCompanyCoreTables,
  createCompanyMaster,
  prepareCompanyOnboarding,
  type CompanyOnboardingPrepareRequest,
} from "@/services/company-service";

export const useProvisionCompany = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ companyId, ...body }: CompanyOnboardingPrepareRequest & { companyId: string }) => {
      const [onboarding] = await Promise.all([
        prepareCompanyOnboarding(companyId, body),
        createCompanyCoreTables(companyId),
        createCompanyMaster({
          company_id: companyId,
          company_name: body.company_name,
          industry_hint: body.industry_hint,
          size_hint: body.size_hint,
        }),
      ]);
      return onboarding;
    },
    onSuccess: () => {
      // The company switcher's list is backend-sourced (see AuthProvider);
      // refetch it now so the just-created company shows up as a real
      // entry instead of relying solely on AuthProvider's optimistic one.
      void queryClient.invalidateQueries({ queryKey: ["companies"] });
    },
  });
};
