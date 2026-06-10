import { z } from "zod";

export const qualityRunSchema = z.object({
  quality_run_id: z.string(),
  quality_score: z.number().int().min(0).max(100),
  release_decision: z.enum(["go", "conditional_go", "no_go"]),
  risk_level: z.enum(["low", "medium", "high"])
});

export type QualityRun = z.infer<typeof qualityRunSchema>;
