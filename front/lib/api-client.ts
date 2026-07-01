import { z } from "zod";

import { env } from "./env";
import { qualityRunSchema } from "./schemas";

const apiBaseUrl = env.apiBaseUrl;

/** GET a JSON resource and validate it against a zod schema. */
export async function apiGet<S extends z.ZodTypeAny>(
  path: string,
  schema: S,
): Promise<z.infer<S>> {
  const response = await fetch(`${apiBaseUrl}${path}`);
  if (!response.ok) {
    throw new Error(`GET ${path} failed: ${response.status}`);
  }
  return schema.parse(await response.json());
}

/** POST a JSON body and validate the response against a zod schema. */
export async function apiPost<S extends z.ZodTypeAny>(
  path: string,
  body: unknown,
  schema: S,
): Promise<z.infer<S>> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new Error(`POST ${path} failed: ${response.status}`);
  }
  return schema.parse(await response.json());
}

// Existing QualityOps helper — retained.
export async function fetchQualityRun(qualityRunId: string) {
  return apiGet(`/quality-runs/${qualityRunId}`, qualityRunSchema);
}
