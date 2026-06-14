<!-- Generated from .ai-common. Do not edit directly. -->

# Design Standard

`DESIGN.md` is the map: what we build and how the pieces fit. Behavior rules live in `AGENTS.md`, procedures in `skills/`, tool permissions in `MCP_POLICY.md`.

## Standard Architecture

```text
front/   Next.js (TypeScript) static export -> Firebase Hosting
back/    FastAPI (Python) on Cloud Run
agent/   ADK + Gemini API on Cloud Run
infra/   Terraform / OpenTofu, Cloud Build, Artifact Registry,
         Firestore, Cloud Storage, Secret Manager
docs/    architecture, operations, security, cost, demo, ADR
```

### Frontend (`front/`)

- Next.js with TypeScript, exported as a static site.
- Deployed to Firebase Hosting.
- Talks to `back/` over HTTPS with typed clients generated from the FastAPI OpenAPI spec.
- Playwright is the source of truth for UI behavior and screenshots used by QualityOps.

### Backend (`back/`)

- FastAPI service hosted on Cloud Run.
- API contracts published as OpenAPI; downstream clients (frontend, agent) regenerate from this.
- Persistence: Firestore for runtime state, Cloud Storage for artifacts.
- Secrets via Secret Manager; never via `.env` committed to the repo.

### Agent (`agent/`)

- ADK orchestrator using the Gemini API.
- Runs on Cloud Run, separately from `back/`, with its own service account.
- All evaluation, scoring, and gate outputs are JSON Schema-validated before they affect a downstream decision.
- Prompt policy, tool permissions, evaluation logic, and runtime orchestration are separated.

### Infra (`infra/`)

- Terraform or OpenTofu as the source of truth for cloud resources.
- Cloud Build for CI image builds; Artifact Registry for container images.
- Cloud Storage buckets carry lifecycle policies for screenshots, traces, and reports.
- Secret Manager holds credentials; service accounts are scoped per workload.

## CI/CD Flow

1. **PR open / update** → triggers `qualityops-ci`, `ai-review`, `security-check` reusable workflows.
2. **Lint + type check** for front, back, agent.
3. **Unit tests** for front, back, agent.
4. **Playwright** runs against a preview build; saves screenshots and traces to Cloud Storage.
5. **AI evaluation** (`quality-evaluation` skill) reads the PR diff plus Playwright evidence and produces a schema-valid report.
6. **Release Gate** (`release-gate` skill) proposes `allow` / `needs_approval` / `block`.
7. **PR Report** (`pr-report` skill) posts the consolidated comment with quality, risk, UI, cost, and gate decision.
8. **Human** reviews the gate decision and approves (or rejects) deploy.
9. **Deploy** is performed by a human-approved workflow only — never auto-triggered by the agent.

## QualityOps Flow

```text
PR created/updated
  ↓
CI runs (lint, type, unit, integration)
  ↓
Playwright saves screenshots / traces to GCS
  ↓
Agent evaluates PR diff + evidence (schema-valid output)
  ↓
Report Agent posts PR comment
  ↓
Release Gate Agent proposes Go / Conditional Go / No-Go
  ↓
Human approves
  ↓
Deploy
```

## Google Cloud Components

- **Cloud Run** for `back/` and `agent/` services (`min=0`, `max=1–2` by default).
- **Firebase Hosting** for the exported Next.js site.
- **Cloud Build** for image build pipelines on push to main and on tag.
- **Artifact Registry** for container images with cleanup policies.
- **Firestore** (Native mode) for runtime state.
- **Cloud Storage** for screenshots, traces, evaluation artifacts, with lifecycle deletion.
- **Secret Manager** for all credentials.
- **Cloud Logging** for sanitized operational logs feeding the QualityOps loop.
- **BigQuery** is optional, behind a project overlay opt-in (cost).

## Cost Assumptions

- USD 300 hard ceiling across all Google Cloud spend, per project, per month.
- Cloud Run min instances 0; max instances 1–2 unless overridden.
- Storage lifecycle deletes Playwright artifacts after a project-defined retention.
- AI calls are quota-bounded per PR and per day; high-cost models are manual.
- Budget alerts notify; they do not auto-stop. Cost Guard checks in CI enforce the gate.

## Security Assumptions

- Service accounts are separated: one for `back/`, one for `agent/`, one for CI.
- The agent service account never has direct production-deploy or IAM permissions.
- All secrets come from Secret Manager at runtime.
- Cloud Run ingress is private or auth-required unless a screen is intentionally public.
- Production endpoints are not directly invoked from MCP tools.

## Observability Assumptions

- Cloud Logging carries sanitized application logs.
- Evaluation runs log inputs, outputs, and version metadata so they can be replayed without secrets.
- PR comments and reports show evidence references, not raw secrets.
- Failed production cases feed back into the test/evaluation corpus after anonymization.

## Project Overlays

`.ai/overlays/DESIGN.project.md` adds project-specific architecture detail (component names, integration partners, screen list). Overlays may extend, not contradict, this base.

