<!-- Generated from .ai-common. Do not edit directly. -->

---
name: playwright-ui-review
description: Review UI clarity, accessibility, error handling, and release risk from Playwright screenshots, traces, DOM, and UI spec. Use for PRs that change user-visible screens.
allowed-tools: Read Grep Bash
---

# Playwright UI Review

UI evaluation from Playwright evidence. Important screens only — not every page on every run.

## Inputs

- Playwright screenshots (desktop + mobile), traces, DOM snapshots.
- Project UI spec or rubric overlay.
- PR diff scoped to `front/`.

## Procedure

1. Identify the user-critical flows the PR changes.
2. Limit the review to those flows + screens called out in the project UI rubric.
3. For each screen, evaluate against the four dimensions:
   1. **UI Clarity** — visual hierarchy, copy, scanability.
   2. **Accessibility** — keyboard, focus order, role/name, contrast, screen-reader basics.
   3. **Error Handling** — loading, empty, error, and recovery states.
   4. **Release Risk** — does this regress an existing critical workflow?
4. Map findings to `rubric.md`.
5. Suggest Playwright assertions that would catch each regression.

## Output

- Reviewed URLs and viewport sizes.
- Screenshot references (path or storage URI; no embedded payloads).
- Findings mapped to `rubric.md` dimensions, with severity.
- Suggested Playwright assertions.

## Guardrails

- Do not capture screenshots from production unless explicitly approved.
- Do not include PII or user identifiers in the report.
- Limit screenshots to critical screens; do not upload bulk pages.
- Compress images before saving artifacts.
