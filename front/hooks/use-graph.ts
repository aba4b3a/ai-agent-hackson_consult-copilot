"use client";

import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@/components/feature/auth/AuthProvider";
import { getGraphData } from "@/services/graph-service";

export const useGraph = () => {
  const { activeCompany } = useAuth();

  return useQuery({
    queryKey: ["knowledge-graph", activeCompany.code],
    queryFn: () => getGraphData(activeCompany.code),
  });
};
