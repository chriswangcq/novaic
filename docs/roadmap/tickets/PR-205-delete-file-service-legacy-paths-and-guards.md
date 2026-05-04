# PR-205 — Delete File Service Legacy Paths and Guardrails

| Field | Value |
| --- | --- |
| Status | `[planned]` |
| Owner | Codex |
| Created | 2026-05-04 |
| Repos | all first-party repos, docs, CI |
| Depends on | PR-204 |
| Theme | Physical deletion |

## Goal

Physically delete old Storage-A/File Service naming and hot paths once BlobRef is the only active path.

## Current-State Analysis

Old path concepts are still present in package names, docs, tests, and examples. They are acceptable during migration only; after PR-204 they become entropy.

## Small Tickets

- [ ] PR-205A — Delete active Storage-A/File Service hot-path code.
- [ ] PR-205B — Rename remaining service/package/docs to Blob Service where still active.
- [ ] PR-205C — Remove Cortex `HttpFileFetcher("storage-a")` style path or replace with Blob resolver.
- [ ] PR-205D — Add static guards banning new `storage-a`, `fs://`, and `/api/files` hot-path writes.

## Done Criteria

- `rg storage-a` only finds migration/archive notes or service deployment name if still unavoidable.
- `rg fs://` does not find new-write active paths.
- `rg /api/files` does not find App/Gateway hot-path construction.
- CI guards fail on legacy resurrection.

## Deployment Checklist

- [ ] All touched repo tests pass.
- [ ] Services deployed.
- [ ] Guardrails wired into CI or equivalent test suite.

