const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
export const companyId = process.env.NEXT_PUBLIC_COMPANY_ID ?? "SMB-1042";

export class ApiError extends Error {
  status: number;

  constructor(status: number, path: string) {
    super(`API error ${status}: ${path}`);
    this.status = status;
  }
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${apiBase}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) throw new ApiError(res.status, path);
  return res.json() as Promise<T>;
}
