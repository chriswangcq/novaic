# Subagent finalize status payload identity

## Problem Definition

`wake_finalize._build_set_sleeping_payload()` and `_build_set_subagent_completed_payload()` currently produce terminal Business status payloads with only coarse `agent_id/subagent_id` identity. This prevents downstream handlers and tests from proving that a status mutation belongs to the current wake/session. P357 only covers payload construction and local builder tests; handler enforcement and DAG ordering are separate child problems.

## Proposed Solution

1. Add a small shared helper in `task_queue/sagas/wake_finalize.py` that builds the terminal subagent lifecycle identity from the finalize context.
2. Include at least `scope_id` and positive `session_generation` in both `set_subagent_sleeping` and `set_subagent_completed` payloads, while preserving:
   - `agent_id`
   - `subagent_id`
   - `result: None` for completed payloads.
3. Reuse the existing `_session_generation(ctx)` helper so missing or non-positive generation fails at payload-build time.
4. Update focused tests around PR-43 legacy last-scope wiring and finalize ownership to assert:
   - identity fields are present.
   - missing or zero generation is rejected.
   - `last_scope_id` and `last_scope_archived_at` are not emitted.

## Acceptance Criteria

- Both terminal status payload builders include `scope_id` and positive `session_generation`.
- Missing or non-positive generation fails before a terminal status task payload can be produced.
- Existing completed-payload `result` semantics remain unchanged.
- Tests prove the new identity contract and the absence of `last_scope_id` payload residue.

## Verification Plan

- `python3 -m py_compile task_queue/sagas/wake_finalize.py`
- `PYTHONPATH=.:../novaic-common pytest -q tests/test_pr43_last_scope_wiring.py tests/test_pr254_finalize_ownership.py tests/test_pr311_saga_compensation_outbox_cutover.py`
- Source guard:
  - no `last_scope_id` in `task_queue/sagas/wake_finalize.py`
  - no `ctx.get("session_generation") or 0` in `task_queue/sagas/wake_finalize.py`

## Risks

- Handler tests may currently expect coarse payloads; those tests should be updated to the new explicit contract instead of keeping compatibility.
- Do not solve handler validation or DAG ordering in this ticket; if payload changes expose those gaps, leave them to P358/P359.

## Assumptions

- `session_generation` in wake-finalize context has already been made mandatory by earlier tickets.
- `scope_id` is the current wake scope identity needed for audit and downstream validation.
