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

export const listWikiFiles = (targetCompanyId = companyId): Promise<WikiFilesResponse> =>
  apiFetch(`/api/v1/companies/${encodeURIComponent(targetCompanyId)}/wiki/files`);

export const listWikiVersions = (targetCompanyId = companyId): Promise<WikiVersionsResponse> =>
  apiFetch(`/api/v1/companies/${encodeURIComponent(targetCompanyId)}/wiki/versions`);

export const readWikiFile = (path: string, version?: string, targetCompanyId = companyId): Promise<WikiFileContent> => {
  const qs = new URLSearchParams({ path });
  if (version) qs.set("version", version);
  return apiFetch(`/api/v1/companies/${encodeURIComponent(targetCompanyId)}/wiki/files/content?${qs.toString()}`);
};
