# PR-152B — Replace Gateway Generic Business Entity Client

| Field | Value |
| --- | --- |
| Status | `[deployed]` |
| Owner | Codex |
| Created | 2026-05-01 |
| Parent | PR-152 |
| Repos | novaic-gateway, novaic-business, docs |

## Goal

Remove Gateway's generic Business entity CRUD client and replace the remaining file metadata use case with an explicit Business file-metadata boundary.

## Why This Matters

A generic `/internal/entities/*` client in Gateway makes Gateway look like a business/entity owner. The only current live use is file proxy metadata, so it should be expressed as a specific file boundary.

## Implementation Plan

1. [x] Add explicit Business internal file metadata endpoints for register/get/delete.
2. [x] Change Gateway file proxy to call those file-specific endpoints.
3. [x] Delete `gateway.infra.business_entity_client`.
4. [x] Remove unused Gateway agent access helper if it only existed for generic entity lookup.
5. [x] Add guardrail that Gateway active code cannot call Business `/internal/entities/*`.

## Unit / Guardrail Tests

- [x] Business file metadata endpoint tests.
- [x] Gateway file metadata client tests or boundary guard.
- [x] Existing targeted Business and Gateway tests pass:
  - Business: `python3 -m pytest tests/test_pr152_file_metadata_boundary.py tests/test_pr151_device_binding_contract.py tests/test_pr141_compat_cleanup.py` → 7 passed.
  - Gateway: `python3 -m pytest tests/test_pr152_gateway_boundary.py tests/test_pr121_gateway_entangled_boundary.py tests/unit/gateway/test_entangled_endpoint_only.py tests/test_pr119_no_legacy_api_schemas.py tests/test_pr141_no_db_access_alias.py` → 18 passed.

## Smoke / Deploy / Git

- [x] Smoke file metadata register/get/delete via unit boundary tests.
- [x] Deploy Business and Gateway.
- [x] Commit in affected subrepos:
  - `novaic-business`: `3100daf business: add explicit file metadata boundary`.
  - `novaic-gateway`: `5af0bc3 gateway: remove generic business entity client`.
- [ ] Parent repo submodule/docs commit and push.
