<!-- Generated from .ai-common. Do not edit directly. -->

# Skills Standard

`SKILLS.md` is an **index**, not a procedure document. The procedure body for each skill lives in `skills/<name>/SKILL.md`.

## Principles

- One skill = one task workflow.
- Skills are Markdown. They are readable by Claude Code, Codex, and Antigravity CLI without translation.
- Long procedures do **not** live in `AGENTS.md`. They live in `skills/<name>/SKILL.md`.
- Side-effecting skills must declare `disable-model-invocation: true` in YAML frontmatter so the harness will not auto-trigger them.
- Skills that read project files only, with no external side effects, may be model-invocable.

## Naming

- Skill directory and `name:` slug are kebab-case (`code-review`, `release-gate`).
- Skill titles are Title Case in the body.
- Supporting files (rubric, checklist, templates) live next to `SKILL.md` and are referenced by relative path.

## Required Frontmatter

```yaml
---
name: skill-name
description: One sentence. Say WHEN to use this skill.
allowed-tools: Read Grep Bash
# Side-effecting skills must add:
disable-model-invocation: true
---
```

## Skill Catalog

| Skill | Side effect | `disable-model-invocation` |
|---|---|---|
| [`code-review`](skills/code-review/SKILL.md) | No | false |
| [`playwright-ui-review`](skills/playwright-ui-review/SKILL.md) | No (local Playwright only) | false |
| [`fastapi-testdata`](skills/fastapi-testdata/SKILL.md) | No | false |
| [`quality-evaluation`](skills/quality-evaluation/SKILL.md) | No | false |
| [`pr-report`](skills/pr-report/SKILL.md) | No (output only; posting handled by workflow) | false |
| [`release-gate`](skills/release-gate/SKILL.md) | Proposes release decision | **true** |
| [`cost-guard`](skills/cost-guard/SKILL.md) | Proposes cost decision | **true** |
| [`terraform-review`](skills/terraform-review/SKILL.md) | Reviews infra plans only | **true** |
| [`cloudrun-deploy-review`](skills/cloudrun-deploy-review/SKILL.md) | Reviews deploy readiness only | **true** |

Deploy, release, Terraform `apply`, IAM changes, and secret operations are **human-approval-only** regardless of which skill surfaces them.

## Supporting Files

Each `skills/<name>/` directory may contain:

- `SKILL.md` — required entry point.
- `checklist.md`, `rubric.md`, `output-schema.json`, `templates/` — referenced by the skill body.

## Project Overlay

`.ai/overlays/skills/<name>/SKILL.md` may add project-specific skills. They follow the same naming and frontmatter rules. They may not weaken side-effect protections.

