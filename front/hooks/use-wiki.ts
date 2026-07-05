import { useQuery } from "@tanstack/react-query";

import { useAuth } from "@/components/feature/auth/AuthProvider";
import { listWikiFiles, listWikiVersions, readWikiFile } from "@/services/wiki-service";

export const useWikiFiles = () => {
  const { activeCompany } = useAuth();

  return useQuery({
    queryKey: ["wiki-files", activeCompany.code],
    queryFn: () => listWikiFiles(activeCompany.code),
    staleTime: 30_000,
  });
};

export const useWikiVersions = () => {
  const { activeCompany } = useAuth();

  return useQuery({
    queryKey: ["wiki-versions", activeCompany.code],
    queryFn: () => listWikiVersions(activeCompany.code),
    staleTime: 30_000,
  });
};

export const useWikiFileContent = (
  path: string | null,
  version: string | undefined,
  enabled: boolean,
) => {
  const { activeCompany } = useAuth();

  return useQuery({
    queryKey: ["wiki-file-content", activeCompany.code, path ?? "", version ?? "current"],
    queryFn: () => readWikiFile(path as string, version, activeCompany.code),
    enabled: enabled && Boolean(path),
    staleTime: 30_000,
  });
};
