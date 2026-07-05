"use client";

import { useMutation } from "@tanstack/react-query";
import {
  createCompanyCoreTables,
  prepareCompanyOnboarding,
  type CompanyOnboardingPrepareRequest,
} from "@/services/company-service";

export const useProvisionCompany = () => {
  return useMutation({
    mutationFn: async ({ companyId, ...body }: CompanyOnboardingPrepareRequest & { companyId: string }) => {
      const [onboarding] = await Promise.all([
        prepareCompanyOnboarding(companyId, body),
        createCompanyCoreTables(companyId),
      ]);
      return onboarding;
    },
  });
};
