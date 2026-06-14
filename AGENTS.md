<!-- Generated from .ai-common. Do not edit directly. -->

# AI Agent Operating Standard

This file is the vendor-neutral top-level rule source for AI development agents working in consumer projects that import this repository as `.ai-common/`.

## Repository Shape

Assume consumer projects have:

- `front/`: React, Next.js, TypeScript frontend
- `back/`: Python, FastAPI backend
- `agent/`: ADK, Gemini API, AI agent implementation
- `infra/`: Terraform or OpenTofu, Cloud Build, Cloud Run, Firebase, IAM
- `docs/`: architecture, operations, security, cost, demo, and ADR material

## Non-Negotiable Rules

- This repository is the shared AI agent operating resource. Treat its standards as the floor, project overlays may only tighten them.
- The primary working scope is the current PR diff. Do not expand scope without explicit instruction.
- Large rewrites, broad refactors, and surrounding cleanup are not allowed unless the user explicitly requests them.
- Do not output, log, embed in prompts, or post to PR comments any secrets, tokens, service account keys, project IDs that are not already public, or PII.
- Production deploy, Terraform `apply`, IAM mutation, Secret Manager value reads, public-access changes, and destructive deletes require explicit human approval. They must never run from an agent autonomously.
- Cost Guard is mandatory. Agents must not bypass it, disable it, or assume "the budget will cover it."
- MCP write operations require explicit human approval each time. MCP is a permission boundary, not a tool catalog.
- All AI/model output that drives a downstream decision must be schema-validated (see `skills/quality-evaluation/output-schema.json`). Unvalidated output is treated as untrusted.
- The Release Gate is advisory. Agents may propose Go / Conditional Go / No-Go, but the final release decision belongs to a human.

## Prohibited Actions

- Production deploy without human approval.
- `terraform apply` / `tofu apply`.
- IAM policy bindings, role grants, or service account key creation.
- Secret value reads via any tool.
- `rm -rf`, `kubectl delete`, bucket lifecycle wipes, force-push to protected branches.
- Disabling Cost Guard, budget checks, or release gate checks.
- Modifying CI/CD or branch-protection rules without explicit instruction.
- Re-running `sync.sh` over a project that has uncommitted edits to generated files without warning the user.

## Human Approval Required

- Any side effect on shared infrastructure (Cloud Run, Cloud Build, Firestore, GCS, Artifact Registry, Firebase Hosting).
- Any change visible to other people (PR comments, Slack, issue updates).
- Any modification of `.github/workflows/` beyond the generated caller files.
- Any deviation from the project overlay budget or skill policy.

## PR Diff First

- Read the PR diff before touching any other file.
- Reason about behavior change before style, then security, then cost, then test coverage.
- Reference findings by `path/to/file.ext:line`.
- Do not introduce features outside the diff scope.

## Secret and PII Protection

- Treat Secret Manager as the only legitimate source of secrets.
- `.env`, service-account JSON, OAuth tokens, and API keys must never be committed.
- Do not include secret or PII strings in logs, prompts, evaluation samples, or PR reports.
- Redact identifiers in production-log replays before they reach evaluation fixtures.

## Cost Guard

- Default Google Cloud budget target is USD 300 or less for the whole project.
- AI calls must be controlled per-PR and per-day. High-cost models run only via explicit human invocation.
- Cloud Run services default to `min_instances=0`; max is recommended 1–2 unless the project overlay raises it.
- Screenshots and traces must be compressed and limited to critical screens.
- Recurring spend changes require Cost Guard sign-off before merging.

## MCP Policy

- Default deny.
- Read-only first.
- Write operations require human approval per invocation.
- Destructive delete, production deploy, secret read, IAM update, and `terraform apply` are excluded from base policy.
- Project overlays may add narrow read-only servers; they may not weaken base prohibitions.

## Schema Validation Of AI Output

- Evaluation, quality scoring, release gate, and cost guard outputs must conform to the JSON schema in `skills/quality-evaluation/output-schema.json`.
- Free-form summaries are allowed alongside structured output but must not replace it.

## Release Gate

- Agents propose `allow`, `block`, or `needs_approval` with evidence.
- Agents do not deploy, tag releases, or move traffic.
- A human reviews the proposal and performs the release action.

## Project Overlays

- Apply `.ai/overlays/AGENTS.project.md` after this file.
- Overlays may add stricter rules or project-specific context. They may not relax base rules.
- See `templates/project-overlay/` for the starter layout.

