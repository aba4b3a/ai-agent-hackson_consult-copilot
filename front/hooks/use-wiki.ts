import { useQuery } from "@tanstack/react-query";

import { listWikiFiles, listWikiVersions, readWikiFile } from "@/services/wiki-service";

export const useWikiFiles = () =>
  useQuery({
    queryKey: ["wiki-files"],
    queryFn: listWikiFiles,
    staleTime: 30_000,
  });

export const useWikiVersions = () =>
  useQuery({
    queryKey: ["wiki-versions"],
    queryFn: listWikiVersions,
    staleTime: 30_000,
  });

export const useWikiFileContent = (
  path: string | null,
  version: string | undefined,
  enabled: boolean,
) =>
  useQuery({
    queryKey: ["wiki-file-content", path ?? "", version ?? "current"],
    queryFn: () => readWikiFile(path as string, version),
    enabled: enabled && Boolean(path),
    staleTime: 30_000,
  });
