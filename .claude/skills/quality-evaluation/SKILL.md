<!-- Generated from .ai-common. Do not edit directly. -->

---
name: quality-evaluation
description: Evaluate API results, UI behavior, and AI output quality. Emits JSON conforming to output-schema.json. Use for every PR.
allowed-tools: Read Grep Bash
---

# Quality Evaluation

Schema-valid evaluation across API, UI, and AI output. Output is the structured input to `release-gate` and `pr-report`.

## Inputs

- PR diff and changed files.
- Test results (unit, integration, end-to-end).
- Playwright UI review findings.
- Schema (`output-schema.json` in this directory).
- Project overlay rubric, if present.

## Procedure

1. Define the evaluation target (which endpoints, screens, AI behaviors) and acceptance criteria.
2. Collect evidence from tests, screenshots, logs, schemas, and model outputs.
3. Score deterministic checks first. Rubric-based judgment fills in subjective dimensions.
4. Aggregate per-dimension scores in `[0, 1]`.
5. Classify findings by severity (`critical`, `high`, `medium`, `low`).
6. Emit JSON that validates against `output-schema.json`.

## Output

```json
{
  "status": "pass | warn | fail",
  "summary": "...",
  "scores": {"api": 0.0, "ui": 0.0, "ai_output": 0.0},
  "findings": [
    {"severity": "high", "title": "...", "evidence": "...", "recommendation": "..."}
  ],
  "releaseGate": {"decision": "allow | block | needs_approval", "reason": "..."}
}
```

## Guardrails

- Output must validate against `output-schema.json`. Unvalidated free-form output is rejected.
- No secrets, tokens, or PII in evidence strings.
- High-cost models are not invoked from this skill automatically.
- A `critical` finding implies at minimum `releaseGate.decision = block`.
