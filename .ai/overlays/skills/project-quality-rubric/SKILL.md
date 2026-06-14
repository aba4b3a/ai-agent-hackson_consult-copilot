---
name: project-quality-rubric
description: Project-specific acceptance criteria applied on top of the base quality-evaluation rubric. Use whenever quality-evaluation runs.
allowed-tools: Read Grep Bash
---

# Project Quality Rubric

Project-specific acceptance criteria. Composes with the base `quality-evaluation` skill.

## Inputs

- Base `quality-evaluation` output (schema-valid JSON).
- This project's critical-workflows list (see `DESIGN.project.md`).

## Procedure

1. Read base quality-evaluation result.
2. Apply project-specific stricter rules below.
3. Report any project rule that flips a base `pass` to `warn` or `block`.

## Project Rules

<!-- Replace placeholders. Each rule should reference a critical screen / endpoint / behavior. -->

- <!-- e.g. "Checkout button must remain visible without scroll on mobile widths >= 360px." -->
- <!-- e.g. "Payment-status API never returns 200 with empty body." -->

## Output

- Adjusted release-gate decision with explicit reasons.

## Guardrails

- No secrets or PII in evidence.
- Project rules may only tighten the base; they may not relax it.
