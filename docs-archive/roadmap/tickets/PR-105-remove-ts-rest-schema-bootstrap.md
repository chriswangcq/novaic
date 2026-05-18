# PR-105 — Remove TS REST schema bootstrap and old guardrails

| Field | Value |
| --- | --- |
| **Ticket** | PR-105 |
| **Status** | `[✓]` |
| **Scope** | `novaic-app`, `docs` |
| **Depends on** | PR-103, PR-104 |
| **Invariant** | TS loads schema from Rust, whose schema comes from Entangled direct WS. No REST fallback exists. |

## Problem

Frontend bootstrap still calls Gateway REST `/api/entangled/schema`, falls back to `/api/entangled-schema`, and invokes `entangled_set_sync_contract_version`. This is old code and masks source-of-truth drift.

## Goal

- Replace TS schema bootstrap with `entangled_wait_schema`.
- Delete REST schema verify script and package command.
- Update tests and docs to say Entangled WS is schema SSOT.
- Physically remove stale fallback code.

## Checklist

- [x] Replace TS schema fetcher with Rust command.
- [x] Remove REST fallback helper and old package script.
- [x] Update tests to assert no bare array and no REST wording.
- [x] Update docs that still describe Gateway REST/AppWS schema parity.
- [x] Run unit tests.
- [x] Run browser smoke test: App initializes with no schema 404.
- [x] Deploy frontend/App artifacts.
- [x] Commit, push, and bump parent repo.

## Closeout

Completed 2026-04-29. Frontend bootstrap now waits for Rust's Entangled WS schema cache; REST schema fallback and verification script were deleted.

## Verification

- `cd novaic-app && npm run test:unit -- src/data/entangled/client.test.ts src/data/entities/entangledEntityContracts.test.ts`
- `cd novaic-app && npm run build`
- `rg -n "/api/entangled/schema|/api/entangled-schema|verify-sync-contract-schema|entangled_set_sync_contract_version" novaic-app docs novaic-gateway Entangled` must show no live old path.
