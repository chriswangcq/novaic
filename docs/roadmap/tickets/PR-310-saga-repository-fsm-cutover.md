# PR-310 — Saga Repository FSM Cutover

Status: Closed

## Goal

Route `SagaRepository` lifecycle operations through Saga FSM transitions.

## Scope

- Change create, claim, mark launched, append step result, complete, fail,
  recover stale, and cancel to append saga events and apply reducer decisions.
- Keep `tq_sagas` as projection-only if still needed by readers.
- Make old imperative lifecycle branches unreachable.

## Explicit Dependency Boundary Review

All non-deterministic values must be supplied at repository boundary:

- current timestamp
- generated saga id
- worker id
- retry/stale policy

## Branch / Old Code Cleanup Ledger

Removed in this PR:

- `SagaRepository.create`, `claim`, `mark_launched`, `append_step_result`,
  `check_saga_complete`, `mark_completed`, `mark_failed`, `recover_stale`, and
  `cancel_all` now decide through `queue_service.saga_fsm`.
- `tq_sagas` is now a runtime projection table for those lifecycle decisions.

Must be removed by follow-up tickets:

- Direct saga compensation side effects in PR-311.
- Residue guards for old direct saga status SQL in PR-312.

## Verification

- `python -m py_compile queue_service/saga_repo.py queue_service/saga_fsm.py queue_service/saga_ledger.py`
- `pytest tests/test_pr310_saga_repository_fsm_cutover.py tests/integration/test_saga_dag_refactor.py tests/integration/test_depends_on_prev_result.py tests/test_queue_explicit_dependencies.py tests/test_pr308_saga_lifecycle_fsm.py tests/test_pr309_saga_fsm_store_ledger.py`
- Re-run with PR-311/312 focused suite: `pytest tests/test_pr312_saga_old_sql_residue_cleanup.py tests/test_pr311_saga_compensation_outbox_cutover.py tests/test_pr310_saga_repository_fsm_cutover.py`

## Closure Notes

Closed. Saga lifecycle state changes now record saga FSM event/state rows and
apply `tq_sagas` writes through a single projection writer. `tq_sagas` is not
deleted yet because workers and API readers still use it as the runtime
projection.
