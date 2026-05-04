# PR-205 — Delete Retired File Paths and Guardrails

| Field | Value |
| --- | --- |
| Status | `[done]` |
| Owner | Codex |
| Created | 2026-05-04 |
| Repos | all first-party repos, docs, CI |
| Depends on | PR-204 |
| Theme | Physical deletion |

## Goal

Physically delete old file-service naming and hot paths once BlobRef is the only active path.

## Current-State Analysis

Old path concepts are still present in package names, docs, tests, and examples. They are acceptable during migration only; after PR-204 they become entropy.

## Small Tickets

- [x] PR-205A — Delete active retired-file hot-path code.
- [x] PR-205B — Rename remaining service/package/docs to Blob Service where still active.
- [x] PR-205C — Remove Cortex `HttpFileFetcher("storage-a")` style path or replace with Blob resolver.
- [x] PR-205D — Add static guards banning retired file-route hot-path writes.

## Done Criteria

- Static guards do not find retired file-route writes in active code.
- New large-object references use Blob refs.
- App/Gateway hot paths do not construct retired file routes.
- CI guards fail on legacy resurrection.

## Deployment Checklist

- [x] All touched repo tests pass.
- [x] Services deployed.
- [x] Guardrails wired into CI or equivalent test suite.

## Implementation Notes

- Blob Service active API now exposes only `/v1/blobs/*`; the retired facade,
  resolver, client, and storage helpers were physically deleted.
- Gateway no longer serves the legacy file proxy routes; it only exposes Blob
  access under `/api/blobs/*`.
- Runtime `display` and `audio_qa` accept Blob refs and fetch Blob bytes through
  Blob Service with tenant headers.
- Cortex file resolver exports/tests were deleted; large payloads remain behind
  Blob refs and are projected through Cortex observation/payload paths.
- Active docs now describe Blob Service and Blob proxy semantics; historical
  migration notes remain only in roadmap tickets.
- Added parent CI guard `scripts/ci/test_no_legacy_file_hot_paths.py` to prevent
  retired hot-path tokens from reappearing in active code.

## Verification

- `novaic-storage-a`: targeted test suite passed.
- `novaic-gateway`: gateway boundary tests passed.
- `novaic-agent-runtime`: display/audio/user-content tests passed.
- `novaic-common`: tool definition and product semantics contract tests passed.
- `novaic-cortex`: payload/projection/tenant tests passed.
- Parent guard `scripts/ci/test_no_legacy_file_hot_paths.py` passed.
