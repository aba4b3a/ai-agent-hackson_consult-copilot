<!-- Generated from .ai-common. Do not edit directly. -->

---
name: pr-report
description: Compose the PR-comment markdown report from quality, UI, security, cost, and release-gate evidence. Output only — posting handled by the workflow.
allowed-tools: Read Grep Bash
---

# PR Report

Produces the consolidated PR comment. Does not post — the workflow posts.

## Inputs

- Quality evaluation JSON (schema-valid).
- Playwright UI review findings.
- Security Reviewer findings.
- Cost Guard decision.
- Release Gate proposal.
- `templates/pr-comment.md`.

## Procedure

1. Read all upstream skill outputs.
2. Populate `templates/pr-comment.md`:
   - Quality score and short summary.
   - Risk list (severity + file:line refs).
   - UI findings (rubric-keyed).
   - Test gap suggestions.
   - Cost Guard decision + projected delta.
   - Release-gate decision + required approvers.
3. Keep total length tight — evidence references, not full payloads.
4. Strip secrets, tokens, project IDs not already public, and PII.
5. Emit the rendered markdown.

## Output

- Rendered PR comment markdown ready for the workflow to post.

## Guardrails

- Do not include secrets, tokens, internal URLs, or PII.
- Do not embed full evaluation payloads — link to artifact references instead.
- Do not auto-post; the workflow handles posting under its scoped token.
