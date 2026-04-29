# PR-103 — Entangled WS schema registered in Rust App cache

| Field | Value |
| --- | --- |
| **Ticket** | PR-103 |
| **Status** | `[✓]` |
| **Scope** | `Entangled/packages/client-rust`, `novaic-app/src-tauri` |
| **Depends on** | PR-102 |
| **Invariant** | Direct Entangled WS `event=schema` is the only schema payload consumed by the App runtime. |

## Problem

The App can receive Entangled direct WS push frames, but the current Rust bridge only processes `sync` frames. Schema registration is still driven by old Gateway/App/TS paths.

## Goal

- Expose Entangled transport push subscription to the App bridge.
- Parse direct WS `event=schema` frames in `EntangledSyncBridge`.
- Register entity schema and `syncContractVersion` in `EntangledState`.
- Expose a Tauri command for TS to wait for the registered schema.

## Checklist

- [x] Add schema snapshot/wait helpers to Rust `EntangledState`.
- [x] Add direct WS push processor for schema frames.
- [x] Extend Rust `EntitySchema` so it preserves fields needed by TS.
- [x] Add/adjust unit tests for schema registration and wait behavior.
- [x] Run unit tests.
- [x] Run smoke test against local or deployed Entangled WS.
- [x] Deploy impacted services/app artifacts.
- [x] Commit, push, and bump parent repo.

## Closeout

Completed 2026-04-29. Entangled Rust/App Rust/frontend deployed; direct Entangled WS schema is now registered in Rust and exposed via `entangled_wait_schema`.

## Verification

- `cd Entangled/packages/client-rust && cargo test`
- `cd novaic-app/src-tauri && cargo test`
- `rg -n "entangled_set_sync_contract_version|default_id_field_for_entity" novaic-app/src-tauri Entangled/packages/client-rust` must find no live old path.
