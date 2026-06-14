<!-- Generated from .ai-common. Do not edit directly. -->

---
name: release-gate
description: Propose Go / Conditional Go / No-Go for a release candidate. Read-only — never deploys. Human approval is required for the final release action.
allowed-tools: Read Grep Bash
disable-model-invocation: true
---

# Release Gate

Advisory skill. Proposes `allow` / `block` / `needs_approval`. Never deploys, tags, or moves traffic.

## Inputs

- CI status (lint, type, unit, integration).
- AI evaluation JSON (schema-valid; see `skills/quality-evaluation/output-schema.json`).
- Security Reviewer findings.
- Cost Guard decision.
- Rollback / disablement plan from the PR description.

## Procedure

1. Verify all required checks have completed.
2. Walk `checklist.md` top to bottom.
3. If any item fails: decision is `block` (hard failure) or `needs_approval` (soft).
4. If all items pass: decision is `allow`.
5. Compose evidence: which check, which finding, which file:line.
6. Name the approver role required for `needs_approval`.

## Output

```json
{
  "decision": "allow | block | needs_approval",
  "reason": "...",
  "evidence": [{"check": "...", "result": "...", "ref": "..."}],
  "requiredApprovers": ["release-manager", "security-reviewer"]
}
```

## Guardrails

- `disable-model-invocation: true` — never auto-triggered by the harness.
- This skill does not deploy, tag, or migrate traffic.
- This skill cannot override a `block` from Security Reviewer or Cost Guardian.
- Approval is per-release, not standing.
