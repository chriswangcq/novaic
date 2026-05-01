# PR-150 — Remove App Deprecated Compatibility Shells

| Field | Value |
| --- | --- |
| Status | `[deployed]` |
| Owner | Codex |
| Created | 2026-05-01 |
| Repos | novaic-app, docs |
| Depends on | PR-149 |

## Goal

Delete frontend compatibility shells that remain only to preserve old imports, especially where the real runtime path has moved to Entangled or direct stores.

## Why This Matters

The App now mostly uses Entangled stores and Rust cache. Files that say "type-only", "deprecated", or "backward-compat imports" continue to look like active APIs and invite new code to depend on old concepts.

## Current Suspects

- `novaic-app/src/db/index.ts`
  - `resetDb()`
  - `getDb()`
  - old IndexedDB wording
- `novaic-app/src/application/logService.ts`
  - deprecated `LogService`
  - debug LLM call wrapper ownership
- `novaic-app/src/services/api.ts`
  - type-only old Gateway API namespace
  - deprecated `AICAgent.devices`
- `novaic-app/src/data/entities/models.ts`
  - `CandidateModelEntity` legacy alias
- `novaic-app/src/utils/subagent.ts`
  - legacy main-agent id normalization.

## Implementation Plan

1. [x] Inventory imports of each compatibility shell.
2. [x] Move still-needed types to current ownership modules.
3. [x] Remove unused debug-only LLM call wrapper.
4. [x] Delete no-op exports and dead compatibility files.
5. [x] Add App guardrail for known deleted compatibility names.

## Unit / Guardrail Tests

- [x] App typecheck passes via `npm run build`.
- [x] App unit tests pass: `npm run test:unit -- --run` → 9 files / 33 tests passed.
- [x] Guardrail rejects reintroducing removed compat exports: `src/types/appCompatGuard.test.ts`.
- [x] Tauri Rust check passes: `cargo check`.

## Smoke / Deploy

- [x] App build passes.
- [x] Frontend OTA deployed to `https://relay.gradievo.com/resource/frontend/v0.3.0/`.
- [x] Desktop app built and installed to `/Applications/ByClaw.app`.
- [x] Smoke evidence: deployed frontend `index.html` returns HTTP 200; desktop bundle and binary exist.

## Git / Merge

- [x] Commit in `novaic-app`: `91a1c9b app: remove deprecated compatibility shells`.
- [x] Parent repo submodule bump / docs commit: `4dec063 roadmap: close PR-150 app compat cleanup`.
- [x] Push `main`.
- [x] Mark this ticket `[deployed]` only after deploy evidence is collected.

## Closeout

Removed App compatibility shells around old API type ownership, no-op DB handles, debug log service, scroll constants, legacy model aliases, old AppBridge request/response RPC, legacy device-binding hook parameters, layout persistence aliases, and VM modal aliases. Current AppBridge is now limited to Gateway push, WebRTC signaling, and Entangled endpoint discovery.
