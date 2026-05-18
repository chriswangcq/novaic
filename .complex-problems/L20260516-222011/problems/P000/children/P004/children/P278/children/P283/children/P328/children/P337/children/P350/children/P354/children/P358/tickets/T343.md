# Subagent finalize status handler validation

## Problem Definition

`handle_subagent_set_sleeping()` and `handle_subagent_set_completed()` still mutate Business subagent status after validating only `agent_id/subagent_id` and `business_client`. P357 made wake-finalize payloads carry `scope_id/session_generation`; P358 must make terminal status handlers reject malformed finalize payloads before `business_client.entity_update()`.

This ticket must not alter non-terminal `set_awake` behavior unless a direct dependency is proven.

## Proposed Solution

1. Add a small terminal-status identity validator in `task_queue/handlers/subagent_handlers.py`.
2. Require `scope_id` to be present and require positive `session_generation` using the shared session generation helper.
3. Call this validator in `handle_subagent_set_sleeping()` and `handle_subagent_set_completed()` before constructing or issuing Business updates.
4. Keep Business update payloads minimal; do not write `scope_id` or `session_generation` into Business unless schema evidence proves those fields are accepted.
5. Update PR-43 handler tests so legacy `last_scope_id` payloads without new identity are rejected rather than ignored-through-mutation.
6. Add explicit tests for missing `scope_id`, missing generation, zero generation, and malformed generation for both terminal handlers.

## Acceptance Criteria

- Sleeping/completed handlers reject missing `scope_id`, missing generation, zero generation, and malformed generation before any Business mutation.
- Valid terminal payloads still update Business status and preserve existing `result` behavior for completed.
- No unknown identity/audit fields are written into Business update payloads.
- `set_awake` remains outside this finalize-only contract unless evidence forces otherwise.
- Legacy `last_scope_id` no longer creates a compatibility mutation path.

## Verification Plan

- `python3 -m py_compile task_queue/handlers/subagent_handlers.py`
- `PYTHONPATH=.:../novaic-common pytest -q tests/test_pr43_last_scope_wiring.py`
- Source guard over `task_queue/handlers/subagent_handlers.py` for:
  - generation defaults such as `or 0`
  - terminal handlers calling `entity_update()` before identity validation.

## Risks

- Existing tests may encode the old behavior that legacy last-scope payloads mutate status. Those tests should be changed to the new no-compatibility contract rather than preserved.
- If another live producer besides wake-finalize sends terminal status tasks without identity, this ticket should expose it through tests or source inspection; do not add fallback.

## Assumptions

- P357 is complete, so normal wake-finalize terminal status payloads now include `scope_id` and positive `session_generation`.
- Stale-generation comparison against session state is handled by P359's ordering/gating work, not by these local handlers.
