<!-- Generated from .ai-common. Do not edit directly. -->

# MCP Policy Standard

MCP is the permission boundary between AI agents and external tools. It is not a list of conveniences.

## Defaults

- **Default deny.** Anything not explicitly allowed is denied.
- **Read-only first.** Start with read-only servers, escalate only with cause.
- **Write requires human approval.** Each write call is approved at invocation time, not pre-approved by class.
- **Destructive operations prohibited.** No `delete`, `wipe`, `truncate`, force-push, or lifecycle-clear via MCP.
- **Production deploy prohibited.** No Cloud Run deploy, Firebase Hosting deploy, traffic shift, or rollback via MCP.
- **Secret read prohibited.** No Secret Manager value access via MCP. Secret existence checks may be allowed if scoped read-only.
- **IAM update prohibited.** No `add-iam-policy-binding`, role grant, service-account-key creation, or workload identity change via MCP.
- **Terraform apply prohibited.** `plan` may be invoked through approved channels; `apply` is human-only.

## Base Active Servers

Only safe local / read-only servers are active in `mcp/mcp.base.json`:

- `filesystem` (read-only, scoped to project root)
- `playwright` (local browser automation against approved preview URLs)

All other servers listed under `mcp/servers/` are **documented policy**, not active. Enabling them is a per-project decision recorded in `.ai/overlays/MCP.project.md`.

## Server Classification

- `read_only`: Safe inspection only. May ship in base.
- `approval_required`: Writes or external side effects. Each call needs human approval. Not in base by default.
- `excluded`: Capability not allowed in the base policy. Production deploy, IAM update, secret read, destructive delete.

## Required Controls

- Every server `mcp/servers/<name>.md` documents: purpose, allowed operations, prohibited operations, required env vars, permission model, audit considerations, project overlay notes.
- Tool invocations should be auditable. Recommend logging tool name, caller, arguments (redacted), and approval evidence.
- Project overlays may **narrow** further. They may not weaken base prohibitions.

## Audit

Tool invocation audit is recommended for any non-`read_only` server: who, what, when, approval reference. The base does not mandate a specific sink, but project overlays should declare one (typically Cloud Logging).

## Project Overlay Extension

`.ai/overlays/MCP.project.md` may:

- Add additional read-only MCP servers (with full server doc).
- Promote a base-documented server (`gcp-logging`, `gcs-artifacts`, `firestore`, `cloud-build`, `billing`, `github`) into the active set, with named approver and audit destination.
- Restrict an active server further (smaller scope, narrower allowlist).

It may not:

- Enable secret read, IAM update, production deploy, terraform apply, or destructive delete.
- Bypass per-call human approval for write operations.

