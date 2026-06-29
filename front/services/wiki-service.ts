import { apiFetch, companyId } from "@/lib/api-client";

export type WikiFile = {
  bucket: string;
  path: string;
  size: number | null;
  updated: string | number | null;
  generation: number | null;
};

export type WikiFilesResponse = {
  company_id: string;
  items: WikiFile[];
};

export type WikiVersionsResponse = {
  company_id: string;
  versions: string[];
};

export type WikiFileContent = {
  company_id: string;
  path: string;
  version: string | null;
  content: string;
};

export const listWikiFiles = (): Promise<WikiFilesResponse> =>
  apiFetch(`/api/v1/companies/${companyId}/wiki/files`);

export const listWikiVersions = (): Promise<WikiVersionsResponse> =>
  apiFetch(`/api/v1/companies/${companyId}/wiki/versions`);

export const readWikiFile = (path: string, version?: string): Promise<WikiFileContent> => {
  const qs = new URLSearchParams({ path });
  if (version) qs.set("version", version);
  return apiFetch(`/api/v1/companies/${companyId}/wiki/files/content?${qs.toString()}`);
};
