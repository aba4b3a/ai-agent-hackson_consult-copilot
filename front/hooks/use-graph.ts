"use client";

import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@/components/feature/auth/AuthProvider";
import { sliceToGraphData } from "@/lib/graph-transform";
import { getGraphSlice } from "@/services/graph-service";

export const useGraph = () => {
  const { activeCompany } = useAuth();

  return useQuery({
    queryKey: ["knowledge-graph-slice", activeCompany.code],
    queryFn: async () => sliceToGraphData(await getGraphSlice(activeCompany.code)),
  });
};
