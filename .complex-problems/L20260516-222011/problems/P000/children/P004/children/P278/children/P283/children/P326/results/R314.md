# Session generation lifecycle and advancement inventory result

## Summary

Completed a bounded generation lifecycle inventory. The active session generation authority is `tq_session_state.generation` through `SessionLedgerRepository` and the generic FSM store. New wake/restart generations are allocated from the ledger with `next_generation(...)`, then carried through durable session outbox/saga context and activated by wake-created observation. One compatibility-shaped fallback was found and flagged: session rebuild uses `context.get("session_generation") or 1` when reconstructing from saga context.

## Done

- Mapped active generation storage: `novaic-agent-runtime/queue_service/db/schema.py` defines `tq_session_state.generation`; `session_ledger.py` wraps it with `SessionLedgerRepository`.
- Mapped generation allocation:
  - `session_ledger.py::next_generation(...)` returns current generation + 1 or starts at 1.
  - `session_repo.py` uses `next_generation(...)` for new wake dispatch and pending restart.
  - `_next_session_generation_after_transaction(...)` reads generation under a global transaction for after-transaction wake planning.
- Mapped activation:
  - `session_wake_plan.py` and `session_effects.py` place `session_generation` / `generation` into wake saga outbox payload/context.
  - `session_observed_events.py` requires wake-created observation `generation`, rejects generation < 1, validates matching starting state, and records active session with that generation.
- Mapped rebuild:
  - `session_rebuild.py` marks active states no-active and reconstructs active rows from running saga contexts.
  - Rebuild records `generation=int(context.get("session_generation") or 1)`, which is a flagged fallback for missing saga context generation.
- Mapped tests/guards around lifecycle:
  - `test_pr251_wake_creation_outbox_cutover.py`
  - `test_pr265_session_restart_context_boundary.py`
  - `test_pr280_session_wake_plan_boundary.py`
  - `test_pr288_session_observed_event_handler.py`
  - `test_pr272_session_active_state_ledger_boundary.py`
  - `test_pr315_queue_fsm_final_residue_guard.py`

## Verification

- Source searches:
  - `rg "generation|next_generation|expected_generation|active_generation|record_active_session|record_no_active|mark_active_states_no_active" ...`
  - `rg "or 1|or 0|generation is required|expected_session_generation|current_session_generation|session_generation\\(|next_generation\\(|active_generation\\(" ...`
- Targeted test command from `novaic-agent-runtime`:
  - `PYTHONPATH=.:../novaic-common pytest -q tests/test_pr251_wake_creation_outbox_cutover.py tests/test_pr265_session_restart_context_boundary.py tests/test_pr280_session_wake_plan_boundary.py tests/test_pr288_session_observed_event_handler.py tests/test_pr272_session_active_state_ledger_boundary.py tests/test_pr315_queue_fsm_final_residue_guard.py`
  - Result: `22 passed in 0.18s`.

## Known Gaps

- `session_rebuild.py` still has a missing-generation fallback: `generation=int(context.get("session_generation") or 1)`. This is flagged for the generation residue/compatibility audit (P329) because it is a compatibility-shaped path that may hide missing saga context generation during rebuild.
- `SessionLedgerRepository.active_generation(...)` returns `max(generation, 1)` when the provided active scope does not match current state. This was not classified here because attach-specific stale-scope behavior belongs to P327.

## Artifacts

- `novaic-agent-runtime/queue_service/db/schema.py`
- `novaic-agent-runtime/queue_service/session_ledger.py`
- `novaic-agent-runtime/queue_service/session_repo.py`
- `novaic-agent-runtime/queue_service/session_wake_plan.py`
- `novaic-agent-runtime/queue_service/session_effects.py`
- `novaic-agent-runtime/queue_service/session_observed_events.py`
- `novaic-agent-runtime/queue_service/session_rebuild.py`
- `novaic-agent-runtime/tests/test_pr251_wake_creation_outbox_cutover.py`
- `novaic-agent-runtime/tests/test_pr288_session_observed_event_handler.py`
- `novaic-agent-runtime/tests/test_pr315_queue_fsm_final_residue_guard.py`
