# PR-152C — Remove Stale AppBridge Request Permission

| Field | Value |
| --- | --- |
| Status | `[closed]` |
| Owner | Codex |
| Created | 2026-05-01 |
| Parent | PR-152 |
| Repos | novaic-app, docs |

## Goal

Remove the stale `gateway_ws_request` Tauri permission and generated ACL residue after the old AppBridge request/response path was deleted.

## Why This Matters

Leaving a permission for a deleted command makes it look like the old AppBridge request/response API still exists. That is exactly the kind of dead branch that misleads future cleanup.

## Implementation Plan

1. [x] Remove `gateway_ws_request` from Tauri permissions.
2. [x] Regenerate or clean generated ACL manifests so the stale command is gone.
3. [x] Add guardrail to prevent the removed command from returning.

## Unit / Guardrail Tests

- [x] App compatibility guard checks no `gateway_ws_request` residue exists in command code, permissions, and generated ACL.
- [x] App unit tests/build pass.
  - `npm run test:unit -- --run src/types/appCompatGuard.test.ts` — 3 passed.
  - `npm run build` — passed.
  - `cargo check` in `src-tauri` — passed with pre-existing warnings.

## Smoke / Deploy / Git

- [x] Smoke App build.
- [x] Deploy frontend/desktop if needed: no OTA change; desktop permission path smoke covered by `npm run build` and `cargo check`.
- [x] Commit in `novaic-app`: `cb17ebf app: remove stale appbridge request permission`.
- [ ] Parent repo submodule/docs commit and push.
