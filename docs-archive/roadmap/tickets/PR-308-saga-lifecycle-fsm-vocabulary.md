# PR-308 — Saga Lifecycle FSM Vocabulary

Status: Closed

## Goal

Introduce an IO-free pure reducer for Saga lifecycle decisions.

## Scope

- Define saga states, events, decisions, and effects.
- Model create, claim, launched, step result, complete, fail, stale recover,
  and cancel.
- Keep compensation effects as output effects, not repository side effects.
- Add table-driven tests and hidden-input guard tests.

## Out Of Scope

- Persistence belongs to PR-309.
- Repository cutover belongs to PR-310.
- Compensation outbox cutover belongs to PR-311.

## Explicit Dependency Boundary Review

Allowed explicit inputs:

- current saga state snapshot
- task completion snapshot
- retry/stale policy snapshot
- failure reason
- compensation policy selected by caller

Forbidden hidden inputs:

- clock/time
- UUID/random IDs
- environment variables
- DB/file/network reads

## Branch / Old Code Cleanup Ledger

Removed in this PR:

- None. Reducer is introduced before cutover.

## Verification

- `pytest tests/test_pr308_saga_lifecycle_fsm.py`
- Hidden input grep on the new reducer.

## Closure Notes

Closed on 2026-05-07.

- Added `queue_service.saga_fsm`, an IO-free pure saga lifecycle reducer.
- Covered create, claim, launch, step result append, complete, fail,
  stale/heartbeat recovery, terminal timeout failure, and cancel transitions.
- Failure decisions can emit explicit compensation effects from caller-provided
  payloads; the reducer itself performs no repository side effects.
- Verification:
  - `python -m py_compile queue_service/saga_fsm.py`
  - `pytest tests/test_pr308_saga_lifecycle_fsm.py`
