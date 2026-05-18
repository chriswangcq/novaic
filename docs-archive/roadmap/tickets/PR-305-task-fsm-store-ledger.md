# PR-305 — Task FSM Store Ledger

Status: Closed

## Goal

Persist task events, task state, and task outbox effects through the generic FSM
store so task lifecycle is durable before `TaskQueue` cutover.

## Scope

- Add task FSM tables or a generic store binding for task machine state.
- Add schema initialization and no-backcompat version bump.
- Add repository helpers for append-event/apply-decision semantics.
- Keep `tq_tasks` as a projection until PR-306/PR-307.

## Out Of Scope

- `TaskQueue` active-path cutover belongs to PR-306.
- Old SQL branch deletion belongs to PR-307.

## Explicit Dependency Boundary Review

The store may use DB, clock, and IDs only through explicit repository
parameters or caller-provided values. The pure reducer remains IO-free.

## Branch / Old Code Cleanup Ledger

Removed in this PR:

- None.

Must be removed by follow-up tickets:

- Direct task status mutation once the projection writer is the only writer.

## Verification

- `pytest tests/test_pr304_task_lifecycle_fsm.py tests/test_pr305_task_fsm_store_ledger.py tests/test_pr259_generic_fsm_store_outbox.py tests/test_pr235_session_ledger.py` — 25 passed.
- Schema initialization now creates `tq_task_events`, `tq_task_state`, and
  `tq_task_outbox` at schema version 15.

## Closure Notes

Added task FSM durable ledger tables and `TaskLedgerRepository` as a thin
adapter over `FsmSqliteStore`. This ticket intentionally does not route
`TaskQueue` through the new ledger; PR-306 owns active-path cutover and PR-307
owns old SQL residue deletion.
