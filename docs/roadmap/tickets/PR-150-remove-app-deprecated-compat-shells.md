# PR-150 — Remove App Deprecated Compatibility Shells

| Field | Value |
| --- | --- |
| Status | `[ ]` |
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

1. [ ] Inventory imports of each compatibility shell.
2. [ ] Move still-needed types to current ownership modules.
3. [ ] Move debug-only LLM call to the Agent Monitor / execution-log module or remove it if unused.
4. [ ] Delete no-op exports and dead compatibility files.
5. [ ] Add App lint/guardrail for known deleted compatibility names.

## Unit / Guardrail Tests

- [ ] App typecheck passes.
- [ ] App unit tests pass.
- [ ] Guardrail rejects reintroducing removed compat exports.

## Smoke / Deploy

- [ ] App build passes.
- [ ] Desktop/frontend deploy.
- [ ] Production smoke: chat, settings cache clear, Agent Monitor, model settings still work.

## Git / Merge

- [ ] Commit in `novaic-app`.
- [ ] Parent repo submodule bump / docs commit.
- [ ] Push `main`.
- [ ] Mark this ticket `[deployed]` only after deploy evidence is collected.

