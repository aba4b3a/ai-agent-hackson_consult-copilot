const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
export const companyId = process.env.NEXT_PUBLIC_COMPANY_ID ?? "SMB-1042";

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${apiBase}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) throw new Error(`API error ${res.status}: ${path}`);
  return res.json() as Promise<T>;
}
