<!-- Generated from .ai-common. Do not edit directly. -->

---
name: code-review
description: Review a PR diff for correctness, tests, types, security, and cost impact. Use when a pull request is opened or updated.
allowed-tools: Read Grep Bash
---

# Code Review

PR-diff-centric review. No large rewrites. No drive-by refactors. No file modifications unless the user explicitly asks for fixes.

## Inputs

- Git diff or pull request reference.
- Project standards (`AGENTS.md`, `DESIGN.md`, `SKILLS.md`, `MCP_POLICY.md`).
- Relevant contracts, schemas, tests.

## Procedure

1. Read the PR diff first. Do not browse the whole repo.
2. Identify changed files, contracts touched, and affected boundaries (front / back / agent / infra).
3. Review **behavior** before style:
   1. Correctness and edge cases.
   2. API / schema compatibility.
   3. Type safety end-to-end.
   4. Error handling and observability.
4. Review security: secrets, auth, injection, log redaction.
5. Review cost: new recurring spend, unbounded loops, model calls, log volume.
6. Review tests: do they cover the changed behavior at the right level?
7. Report findings by severity with `path/to/file.ext:line` references.

## Output

Use `checklist.md` as the field list. Emit:

- Findings (severity: critical / high / medium / low; file:line; evidence; recommendation).
- Open questions.
- Test gaps.
- One-paragraph summary.

## Guardrails

- Do not propose surrounding cleanup or refactor outside the diff.
- Do not modify files in this skill — leave fixes for a follow-up task.
- Do not include secrets or full payloads in findings.
- Escalate any `critical` finding as a release-gate `block`.
