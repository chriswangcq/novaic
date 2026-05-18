# PR-234A — Cortex Authoritative Stack Source

| Field | Value |
| --- | --- |
| Status | `[x]` |
| Parent | PR-234 |
| Scope | `novaic-cortex` |

## Current State

`/v1/context/status` already uses `_collect_active_stack()` for control stack, but `/v1/context/prepare_for_llm` still returns `ContextEngine.status(...).frames`. `ContextEngine.status()` walks render/open-scope nodes and can include stale sibling scopes. `skill_end` validates against `resolve_active_scope_path()` / `_collect_active_stack()`.

## Objective

Make `prepare_for_llm.stack` use the same authoritative active-path stack as `status` and `skill_end`.

## Small Tickets

- `[x]` Replace `prepare_for_llm` stack output with `_collect_active_stack(ws, root_path)`.
- `[x]` Add drift logging/metric when render stack differs from control stack.
- `[x]` Add structured `error_code`, requested id, and actual stack top to `skill_end` logical failures.
- `[x]` Add Cortex tests for drifted sibling open scopes and `skill_end` mismatch payload shape.

## Acceptance Criteria

- A drifted render stack cannot become the prompt Active skill stack.
- Mismatch result has machine-readable error identity.
- Tests do not depend on filesystem temp paths or ambient process state.

## Verification

- `cd novaic-cortex && pytest tests/test_pr234_control_stack.py`
