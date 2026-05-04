# PR-202 — Cortex Payload Blob Externalization

| Field | Value |
| --- | --- |
| Status | `[planned]` |
| Owner | Codex |
| Created | 2026-05-04 |
| Repos | `novaic-cortex`, `novaic-agent-runtime`, `novaic-common`, docs |
| Depends on | PR-201 |
| Theme | Cortex trace stays semantic |

## Goal

Keep Cortex as the work-trace and scope system, while storing large raw payload bytes in Blob Service and retaining only observation summaries plus `payload_ref`.

## Current-State Analysis

Cortex currently writes payload records into its own scope-local payload store through `Workspace.write_payload`. This is not Storage-A, but it still means Cortex owns large payload storage directly.

## Small Tickets

- [ ] PR-202A — Define size thresholds and blob payload policy.
- [ ] PR-202B — Write large tool payloads to Blob Service and store `blob://cortex-payload/...` in Cortex.
- [ ] PR-202C — Update payload read/search/summarize/qa resolver to support BlobRef.
- [ ] PR-202D — Add invariants: default prompt context never includes raw Blob payload.

## Done Criteria

- Small bounded observations remain in Cortex.
- Large payloads are externalized to Blob Service.
- Payload tools can resolve BlobRef explicitly.
- No automatic payload summary or fallback path is added.

## Deployment Checklist

- [ ] Cortex tests pass.
- [ ] Runtime payload tool tests pass.
- [ ] Cortex and Runtime deployed.
- [ ] Smoke: large shell/tool output produces observation plus BlobRef.

