# PR-152 — Gateway / Business / Entangled Boundary Review

| Field | Value |
| --- | --- |
| Status | `[deployed]` |
| Owner | Codex |
| Created | 2026-05-01 |
| Repos | novaic-gateway, novaic-business, Entangled, novaic-app, docs |
| Depends on | PR-151 |

## Goal

Confirm and enforce the boundary that Gateway is only a thin edge layer: sync endpoint discovery, Auth, App WS, file proxy, and WebRTC signaling. Gateway must not regrow schema authority, business orchestration, entity semantics, or Entangled fallback paths.

## Why This Matters

Gateway sits at the boundary between the app, business APIs, and Entangled sync. If it starts duplicating Business or Entangled responsibilities, old schema fallback and proxy branches can silently return.

## Required Process

For this big ticket:

1. Analyze the current live code and deployed behavior.
2. Create small implementation tickets for any concrete cleanup found.
3. Implement each small ticket one by one.
4. Confirm whether the boundary is closed.
5. If not closed, return to step 3; otherwise close this ticket and move to PR-153.

## Boundary Invariant

Gateway may own:

- Auth / token validation.
- App WS connection and broadcast plumbing.
- Entangled sync endpoint discovery.
- File proxy edge routing.
- WebRTC signaling.

Gateway must not own:

- Entangled schema authority.
- Entity business semantics.
- Agent/session orchestration.
- Tool schema generation.
- Business fallback APIs.
- Direct product-state mutation except explicit edge transport responsibilities.

## Small Tickets

- [x] [PR-152A — Remove Gateway Startup Business State Mutation](PR-152A-remove-gateway-startup-business-state.md)
- [x] [PR-152B — Replace Gateway Generic Business Entity Client](PR-152B-replace-gateway-generic-business-entity-client.md)
- [x] [PR-152C — Remove Stale AppBridge Request Permission](PR-152C-remove-stale-appbridge-request-permission.md)

## Current-State Analysis

2026-05-01 scan found:

1. Gateway already has good Entangled endpoint guardrails: App WS sends only `entangled_endpoint`, not schema, and Gateway has no Entangled HTTP/schema library dependency.
2. Gateway startup still lists `agents` through Business and upserts `agent-state`, which is business lifecycle mutation.
3. Gateway still contains a generic `GatewayBusinessEntityClient` for `/internal/entities/*`; live usage is file metadata plus an unused agent access helper.
4. App Tauri permissions still include stale `gateway_ws_request`, even though the old command path has been removed.

These are small enough to close under PR-152 before moving to PR-153.

## Unit / Guardrail Tests

- [x] Add tests or guardrails for any deleted boundary violations.
- [x] Ensure Gateway tests cover the remaining sync endpoint discovery contract.
- [x] Ensure App/Business tests still pass for affected routes.

Evidence:

- Gateway: `python3 -m pytest tests/test_pr152_gateway_boundary.py tests/test_pr121_gateway_entangled_boundary.py tests/unit/gateway/test_entangled_endpoint_only.py tests/test_pr119_no_legacy_api_schemas.py tests/test_pr141_no_db_access_alias.py` — 18 passed.
- Business: `python3 -m pytest tests/test_pr152_file_metadata_boundary.py tests/test_pr151_device_binding_contract.py tests/test_pr141_compat_cleanup.py` — 7 passed.
- App: `npm run test:unit -- --run src/types/appCompatGuard.test.ts` — 3 passed; `npm run build` passed; `cargo check` passed with pre-existing warnings.

## Smoke / Deploy

- [x] Smoke Gateway health and App WS path.
- [x] Smoke Entangled direct sync endpoint discovery.
- [x] Deploy affected services.
- [x] Verify no old schema/business fallback path remains active.

Deploy evidence:

- `./deploy gateway` restarted Entangled, Gateway, Business, Device, Queue, File Service, and Cortex successfully.
- `./deploy status` shows all backend ports healthy and relay active.

## Git / Merge

- [x] Each small ticket can be committed independently where practical.
- [ ] Parent repo submodule bump / docs commit.
- [ ] Push `main`.
- [x] Mark `[deployed]` only after deploy evidence is collected.
