<!-- Generated from .ai-common. Do not edit directly. -->

---
name: cloudrun-deploy-review
description: Review Cloud Run deploy readiness — min/max instances, timeout, auth, ingress, service account, secrets. Never deploys.
allowed-tools: Read Grep Bash
disable-model-invocation: true
---

# Cloud Run Deploy Review

Pre-deploy readiness review. Never executes `gcloud run deploy`, `gcloud run services update`, traffic migration, or rollback.

## Inputs

- Cloud Run service config (Terraform or `service.yaml`).
- Image reference and provenance.
- Service account binding.
- Project overlay deploy policy.

## Procedure

1. Read the proposed service config.
2. Walk `checklist.md`:
   1. **Image** — built in this project's Cloud Build; tag is a content digest or signed; not `:latest`.
   2. **Min instances** — `0` unless project explicitly justifies warm capacity.
   3. **Max instances** — within project ceiling (default 1–2).
   4. **Timeout** — bounded; not the platform max.
   5. **Auth** — `--no-allow-unauthenticated` unless screen is intentionally public.
   6. **Ingress** — `internal` or `internal-and-cloud-load-balancing` unless public.
   7. **Service account** — least-privilege; separate for `back/` and `agent/`.
   8. **Env vars** — referenced from Secret Manager; no plaintext secrets.
   9. **Logging** — sanitized, no PII.
   10. **Rollback target** — previous revision identified and reachable.
   11. **Traffic migration** — gradual where supported; explicit plan.
3. Emit approval requirements and blockers.

## Output

- Decision: `ready` / `not_ready`.
- Blockers list per checklist item.
- Required approver roles before the actual deploy may proceed.
- Rollback target (revision name).

## Guardrails

- `disable-model-invocation: true` — never auto-triggered by the harness.
- This skill does not deploy, update services, or migrate traffic.
- `:latest` image tag → automatic `not_ready`.
- Unauthenticated public ingress on a non-public screen → `not_ready`.
