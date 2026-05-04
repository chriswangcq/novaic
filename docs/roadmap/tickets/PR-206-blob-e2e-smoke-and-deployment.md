# PR-206 — Blob End-to-End Smoke and Deployment Closure

| Field | Value |
| --- | --- |
| Status | `[planned]` |
| Owner | Codex |
| Created | 2026-05-04 |
| Repos | all touched repos |
| Depends on | PR-199..PR-205 |
| Theme | Production closure |

## Goal

Close the Blob Service migration by proving the real product path works end to end.

## Current-State Analysis

The migration spans App, Gateway, Business, Runtime, Cortex, and Blob Service. Unit tests are necessary but not sufficient; a cross-service smoke is required.

## Small Tickets

- [ ] PR-206A — App uploads a user attachment and receives BlobRef.
- [ ] PR-206B — Agent observes attachment/tool artifact and Cortex stores observation plus payload BlobRef.
- [ ] PR-206C — Agent Monitor displays semantic activity and never leaks raw blob payload.
- [ ] PR-206D — Clear local App DB and confirm Entangled resync plus Blob access still work.
- [ ] PR-206E — Production config scan confirms old file/storage switches cannot revive.

## Done Criteria

- Full upload/read/preview/download path works.
- Runtime/Cortex large payload path works.
- Agent Monitor remains user-facing.
- Old branches are absent or guarded.
- Deploy evidence is recorded.

## Deployment Checklist

- [ ] All service deploys completed.
- [ ] Smoke evidence captured.
- [ ] Parent repo submodule pointers pushed.
- [ ] Oclow/backend architecture docs updated if needed.

