# PR-147 — Remove Cortex Disabled / No-op Runtime Path

| Field | Value |
| --- | --- |
| Status | `[ ]` |
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

1. [ ] Remove the runtime no-op CortexBridge path.
2. [ ] Remove or fail-fast any `bridge.enabled == False` handler branches.
3. [ ] Remove the `cortex.enabled=false` config switch if no live deployment requires it.
4. [ ] Replace disabled-path tests with fail-fast invariant tests.
5. [ ] Add guardrail that runtime code cannot contain `Cortex disabled`, `_noop`, or disabled-success handling in active paths.

## Unit / Guardrail Tests

- [ ] Runtime unit tests cover missing Cortex config / failed Cortex calls as hard failures.
- [ ] Runtime saga tests still pass for normal scope lifecycle.
- [ ] Guardrail test rejects reintroducing Cortex disabled/no-op branches.

## Smoke / Deploy

- [ ] Runtime test suite passes.
- [ ] Cortex test suite passes where touched.
- [ ] Deploy Runtime.
- [ ] Deploy services if shared config changes.
- [ ] Production smoke: user message creates wake scope, LLM sees Active scope stack, `skill_end` closes wake scope.
- [ ] Production log evidence: no `Cortex disabled` / no-op messages on the active path.

## Git / Merge

- [ ] Commit in each touched repo.
- [ ] Parent repo submodule bump / docs commit.
- [ ] Push `main`.
- [ ] Mark this ticket `[deployed]` only after deploy evidence is collected.

