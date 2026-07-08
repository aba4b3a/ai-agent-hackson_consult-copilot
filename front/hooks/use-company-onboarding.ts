"use client";

import { useMutation } from "@tanstack/react-query";
import {
  createCompanyCoreTables,
  createCompanyMaster,
  prepareCompanyOnboarding,
  type CompanyOnboardingPrepareRequest,
} from "@/services/company-service";

export const useProvisionCompany = () => {
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
  });
};
