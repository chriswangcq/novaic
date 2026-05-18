# PR-147 — Remove Cortex Disabled / No-op Runtime Path

| Field | Value |
| --- | --- |
| Status | `[deployed]` |
| Owner | Codex |
| Created | 2026-05-01 |
| Repos | novaic-agent-runtime, novaic-common, docs |
| Depends on | PR-146 |

## Goal

Make Cortex a required backend dependency for the Agent runtime path. Runtime must fail loudly when Cortex is unavailable or disabled, instead of pretending scope creation, context assembly, skill lifecycle, or stack checks succeeded.

## Why This Matters

Cortex is the minimal structure owner: LIFO scope tree plus LLM context assembly. A disabled/no-op Cortex branch creates a second semantic path where the agent can appear to run without the structure that gives it continuity. That branch has unclear product value and high debugging risk.

## Current Suspects

- `novaic-agent-runtime/task_queue/utils/cortex_bridge.py`
  - `ServiceConfig.CORTEX_ENABLED`
  - `_noop(...)`
  - `enabled` checks returning empty data or `{"ok": false, "error": "Cortex disabled"}`
- `novaic-agent-runtime/task_queue/handlers/cortex_handlers.py`
  - soft success for `bridge.enabled == False`
  - `check_stack` disabled branch returning empty stack
- `novaic-common/common/config.py`
  - `CORTEX_ENABLED`
- Tests that encode disabled/no-op behavior.

## Implementation Plan

1. [x] Remove the runtime no-op CortexBridge path.
2. [x] Remove or fail-fast any `bridge.enabled == False` handler branches.
3. [x] Remove the `cortex.enabled=false` config switch.
4. [x] Replace disabled-path tests with fail-fast invariant tests.
5. [x] Add guardrail that runtime code cannot contain `Cortex disabled`, `_noop`, or disabled-success handling in active paths.

## Unit / Guardrail Tests

- [x] Runtime unit tests cover the required CortexBridge construction path.
- [x] Runtime saga tests still pass for normal scope lifecycle.
- [x] Guardrail test rejects reintroducing Cortex disabled/no-op branches.

## Smoke / Deploy

- [x] Runtime test suite passes.
- [x] Common config tests pass.
- [x] Deploy Runtime.
- [x] Deploy shared `novaic-common` with Runtime.
- [x] Production smoke: backend status green, Cortex/Queue health endpoints return OK.
- [x] Production log evidence: no `Cortex disabled` / no-op messages in recent active logs.

## Git / Merge

- [x] Commit in each touched repo.
- [x] Parent repo submodule bump / docs commit.
- [x] Push `main`.
- [x] Mark this ticket `[deployed]` only after deploy evidence is collected.

## Evidence

- Runtime targeted tests: `21 passed`.
- Runtime full tests: `199 passed`.
- Common config tests: `12 passed`.
- Deployed via `./deploy runtime`; all api services restarted successfully.
- Production health:
  - Cortex: `{"status":"ok","service":"cortex"}`
  - Queue: `{"status":"healthy","service":"queue-service","version":"1.0.0",...}`
