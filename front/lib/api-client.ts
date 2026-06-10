import { qualityRunSchema } from "./schemas";

const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export async function fetchQualityRun(qualityRunId: string) {
  const response = await fetch(`${apiBaseUrl}/quality-runs/${qualityRunId}`);

  if (!response.ok) {
    throw new Error(`Failed to fetch quality run: ${response.status}`);
  }

  return qualityRunSchema.parse(await response.json());
}
