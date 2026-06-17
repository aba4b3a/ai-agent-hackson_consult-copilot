"use client";

import { useQuery } from "@tanstack/react-query";
import { getGraphData } from "@/services/graph-service";

export const useGraph = () => {
  return useQuery({
    queryKey: ["knowledge-graph"],
    queryFn: getGraphData,
  });
};
