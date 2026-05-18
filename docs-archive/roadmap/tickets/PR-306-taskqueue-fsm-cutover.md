# PR-306 — TaskQueue FSM Cutover

Status: Closed

## Goal

Route `TaskQueue` lifecycle operations through the task FSM transition path.

## Scope

- Change publish, claim, complete, fail, recover stale, release, and cancel to
  append explicit task events and apply task FSM decisions.
- Keep direct `tq_tasks` writes only as projection writes if a projection table
  is still needed.
- Preserve existing external behavior while changing the internal authority.

## Out Of Scope

- Residue deletion belongs to PR-307.

## Explicit Dependency Boundary Review

All non-deterministic values must be supplied at Queue boundary:

- current timestamp
- retry delay timestamp
- worker id
- generated task id

## Branch / Old Code Cleanup Ledger

Removed in this PR:

- Some direct SQL decision branches may be converted to projection writes.

Must be removed by follow-up tickets:

- Any remaining direct status mutation that is not a projection writer.

## Verification

- `pytest tests/test_pr306_taskqueue_fsm_cutover.py tests/test_queue_explicit_dependencies.py tests/integration/test_saga_dag_refactor.py` — 10 passed.
- `pytest tests/unit/task_queue tests/test_pr306_taskqueue_fsm_cutover.py tests/test_queue_explicit_dependencies.py tests/integration/test_saga_dag_refactor.py` — 52 passed.
- New regression tests prove publish/claim/complete/fail/recover/cancel record
  task FSM events and state.

## Closure Notes

`TaskQueue` now owns a `TaskLedgerRepository` and records task FSM events/state
for publish, claim, complete, retry failure, terminal failure, stale recovery,
release, and cancel. Status projection writes are now fed by task FSM decisions
for lifecycle transitions. PR-307 remains responsible for residue cleanup and
static guards around direct task SQL branches.
