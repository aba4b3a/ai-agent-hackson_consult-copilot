import { useQuery } from "@tanstack/react-query";
import { getKnowledgeData } from "@/services/knowledge-service";

export const useKnowledge = () => {
  return useQuery({
    queryKey: ["knowledge"],
    queryFn: () => getKnowledgeData(),
  });
};
