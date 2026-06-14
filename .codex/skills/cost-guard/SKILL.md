<!-- Generated from .ai-common. Do not edit directly. -->

---
name: cost-guard
description: Review AI call, Cloud Run, Cloud Build, Storage, and BigQuery cost impact against the USD 300 Google Cloud ceiling. High-cost actions trigger warnings.
allowed-tools: Read Grep Bash
disable-model-invocation: true
---

# Cost Guard

Reviews cost impact of a PR. Emits `pass` / `warn` / `block`. Never mutates billing settings, quotas, infrastructure, or budgets.

## Inputs

- `budget-policy.md` (this directory).
- `.ai/overlays/COST_GUARD.project.md` if present.
- Terraform plan output (read-only).
- AI call usage projection from `agent/`.
- Current billing snapshot if `billing` MCP server is enabled.

## Procedure

1. Read base + project budget policy.
2. Identify new or changed cloud resources from the PR diff.
3. Estimate recurring monthly delta:
   - Cloud Run (min/max instances, CPU, concurrency).
   - Cloud Build (frequency, machine type).
   - Cloud Storage (volume + lifecycle).
   - Firestore (reads, writes, indexes).
   - BigQuery (queries, storage; opt-in only).
   - Logging (volume, retention).
   - AI calls (model class × tokens × frequency).
4. Sum delta with current month-to-date.
5. Apply decision:
   - Below project ceiling → `pass` (or `warn` if within 80%).
   - Above project ceiling → `block`.
   - Includes high-cost model use → at least `warn`.
   - Unbounded loops, retries, or schedules → `block` until bounded.
6. Emit decision with per-resource evidence.

## Output

```json
{
  "decision": "pass | warn | block",
  "projectedMonthlyDeltaUsd": 0,
  "projectedMonthlyTotalUsd": 0,
  "ceilingUsd": 300,
  "concerns": [{"resource": "...", "issue": "...", "evidence": "..."}],
  "requiredActions": ["..."]
}
```

## Guardrails

- `disable-model-invocation: true` — never auto-triggered by the harness.
- This skill does not change billing, quotas, infra, or budgets.
- High-cost model usage is `warn` minimum, `block` without explicit human invocation.
- Budget alerts are notifications. This skill is the enforcement point.
