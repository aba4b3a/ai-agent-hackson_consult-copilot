import { z } from "zod";

/**
 * Typed, validated access to the public runtime configuration.
 *
 * Next.js inlines `NEXT_PUBLIC_*` variables at build time, so they must be
 * referenced literally (not via a dynamic key). `mockMode` defaults to true so
 * the UI runs against local fixtures without a backend; when it is false a
 * valid API base URL is required.
 */
const rawSchema = z.object({
  NEXT_PUBLIC_API_BASE_URL: z.string().url().optional(),
  NEXT_PUBLIC_MOCK_MODE: z.enum(["true", "false"]).optional(),
});

const parsed = rawSchema.parse({
  NEXT_PUBLIC_API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL,
  NEXT_PUBLIC_MOCK_MODE: process.env.NEXT_PUBLIC_MOCK_MODE,
});

const mockMode = parsed.NEXT_PUBLIC_MOCK_MODE !== "false";

if (!mockMode && !parsed.NEXT_PUBLIC_API_BASE_URL) {
  throw new Error(
    "NEXT_PUBLIC_API_BASE_URL is required when NEXT_PUBLIC_MOCK_MODE is false.",
  );
}

export const env = {
  /** When true, services read from local fixtures instead of the backend. */
  mockMode,
  /** Backend base URL used by the API client when not in mock mode. */
  apiBaseUrl: parsed.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000",
} as const;
