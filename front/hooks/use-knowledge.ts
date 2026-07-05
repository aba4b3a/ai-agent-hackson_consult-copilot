import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@/components/feature/auth/AuthProvider";
import { getKnowledgeData, getKpiTrends } from "@/services/knowledge-service";

export const useKnowledge = () => {
  const { activeCompany } = useAuth();

  return useQuery({
    queryKey: ["knowledge", activeCompany.code],
    queryFn: () => getKnowledgeData(activeCompany.code),
  });
};

export const useKpiTrends = () => {
  const { activeCompany } = useAuth();

  return useQuery({
    queryKey: ["kpi-trends", activeCompany.code],
    queryFn: () => getKpiTrends(activeCompany.code),
  });
};
