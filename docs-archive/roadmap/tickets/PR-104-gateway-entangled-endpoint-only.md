# PR-104 — Gateway AppWS sends only Entangled endpoint

| Field | Value |
| --- | --- |
| **Ticket** | PR-104 |
| **Status** | `[✓]` |
| **Scope** | `novaic-gateway`, `novaic-app/src-tauri` |
| **Depends on** | PR-103 |
| **Invariant** | Gateway is transport discovery only; it is not an Entangled schema source. |

## Problem

Gateway AppWS currently pushes `event=schema` with `entities`, `hash`, `syncContractVersion`, and `entangledWsUrl`. That makes Gateway a competing schema authority.

## Goal

- Replace Gateway AppWS schema push with an endpoint-only event.
- Update AppBridge to start Entangled direct WS from that endpoint-only event.
- Remove Gateway sync-contract parity tests and schema-push wording from active code paths.

## Checklist

- [x] Remove Gateway AppWS schema serialization.
- [x] Remove Gateway dependency on `gateway.entity.sync_contract` for AppWS bootstrap.
- [x] Update AppBridge event handling to consume endpoint-only bootstrap.
- [x] Add tests/guardrails that Gateway AppWS does not push schema entities.
- [x] Run unit tests.
- [x] Run AppWS smoke test.
- [x] Deploy Gateway/App impacted artifacts.
- [x] Commit, push, and bump parent repo.

## Closeout

Completed 2026-04-29. Gateway AppWS now sends only `entangled_endpoint`; `gateway.entity.sync_contract` and obsolete AppWS sync/schema tests were physically removed.

## Verification

- `cd novaic-gateway && python -m pytest tests/unit/gateway`
- `rg -n "event.*schema|syncContractVersion|get_schema\\(" novaic-gateway/gateway/api novaic-app/src-tauri/src/core/app_bridge.rs` must not show Gateway schema bootstrap.
- Production/browser console must not show `/api/entangled/schema` or Gateway schema 404.
