import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@/components/feature/auth/AuthProvider";
import { getKnowledgeData } from "@/services/knowledge-service";

export const useKnowledge = () => {
  const { activeCompany } = useAuth();

  return useQuery({
    queryKey: ["knowledge", activeCompany.code],
    queryFn: () => getKnowledgeData(activeCompany.code),
  });
};
