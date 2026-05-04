# PR-201 — Unified ResourceRef Blob URI Cutover

| Field | Value |
| --- | --- |
| Status | `[planned]` |
| Owner | Codex |
| Created | 2026-05-04 |
| Repos | `novaic-common`, `novaic-business`, `novaic-agent-runtime`, `novaic-cortex`, `novaic-app`, docs |
| Depends on | PR-199, PR-200 |
| Theme | Resource reference SSOT |

## Goal

Make `blob://{namespace}/{blob_id}` the only new large-object reference shape across services.

## Current-State Analysis

Current paths still include `fs://` for Storage-A files and `payload_ref` values for Cortex payloads. These are separate concepts and should converge through a shared ResourceRef parser and ownership model.

## Small Tickets

- [ ] PR-201A — Add shared ResourceRef helpers for BlobRef adoption.
- [ ] PR-201B — Update Runtime/App/Business new writes to store blob refs where large objects are involved.
- [ ] PR-201C — Mark `fs://` as historical/import-only in active docs.
- [ ] PR-201D — Add guard preventing new hot-path `fs://` writes.

## Done Criteria

- New large-object refs use `blob://`.
- Existing `fs://` reads are either migrated or explicitly isolated behind one import/compat boundary.
- Guardrails prevent new code from producing `fs://` on active paths.

## Deployment Checklist

- [ ] Affected services tested.
- [ ] Affected services deployed.
- [ ] Smoke: App attachment path and Runtime artifact path return BlobRef.

