# PR-309 — Saga FSM Store Ledger

Status: Closed

## Goal

Persist saga events, saga state, and saga lifecycle effects through the generic
FSM store.

## Scope

- Add saga FSM store binding and schema.
- Persist reducer decisions atomically with effects.
- Keep `tq_sagas` as a projection until cutover and cleanup.

## Explicit Dependency Boundary Review

The store may use DB only as an explicit boundary. Clock, IDs, and retry
timestamps are caller-provided.

## Branch / Old Code Cleanup Ledger

Removed in this PR:

- None.

Must be removed by follow-up tickets:

- Direct `tq_sagas` lifecycle mutation branches.

## Verification

- Saga FSM store tests.
- Schema initialization tests.

## Closure Notes

Closed on 2026-05-07.

- Added v16 saga FSM ledger tables:
  `tq_saga_events`, `tq_saga_state`, and `tq_saga_outbox`.
- Added `queue_service.saga_ledger`, a thin identity adapter over the generic
  `FsmSqliteStore`.
- Saga state projection JSON (`context`, `step_results`) is encoded/decoded at
  the explicit repository boundary. The generic store remains business-agnostic.
- Verification:
  - `python -m py_compile queue_service/saga_fsm.py queue_service/saga_ledger.py queue_service/db/schema.py`
  - `pytest tests/test_pr308_saga_lifecycle_fsm.py tests/test_pr309_saga_fsm_store_ledger.py`
