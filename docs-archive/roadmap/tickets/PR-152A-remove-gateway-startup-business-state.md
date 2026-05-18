# PR-152A — Remove Gateway Startup Business State Mutation

| Field | Value |
| --- | --- |
| Status | `[deployed]` |
| Owner | Codex |
| Created | 2026-05-01 |
| Parent | PR-152 |
| Repos | novaic-gateway, docs |

## Goal

Delete Gateway startup logic that lists agents through Business and upserts `agent-state`.

## Why This Matters

Gateway startup must not mutate Agent business state. Gateway should be a thin edge process; Agent lifecycle belongs to Business/Queue/Runtime/Cortex.

## Implementation Plan

1. [x] Remove `initialize_systems()` business entity usage from `main_gateway.py`.
2. [x] Keep Gateway startup limited to config validation, auth DB init, local auth tables, App WS, file proxy, and endpoint discovery.
3. [x] Add/adjust Gateway boundary guardrails so startup cannot call Business entity CRUD for Agent state.

## Unit / Guardrail Tests

- [x] Gateway tests prove no startup `agent-state` mutation remains.
- [x] Existing Gateway boundary tests pass: `python3 -m pytest tests/test_pr152_gateway_boundary.py tests/test_pr121_gateway_entangled_boundary.py tests/unit/gateway/test_entangled_endpoint_only.py tests/test_pr119_no_legacy_api_schemas.py tests/test_pr141_no_db_access_alias.py` → 17 passed.

## Smoke / Deploy / Git

- [x] Smoke Gateway health.
- [x] Deploy Gateway if code changes are made.
- [x] Commit in `novaic-gateway`: `caf17f3 gateway: remove startup business state mutation`.
- [ ] Parent repo submodule/docs commit and push.
