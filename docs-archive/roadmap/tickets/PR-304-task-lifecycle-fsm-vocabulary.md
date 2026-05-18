# PR-304 — Task Lifecycle FSM Vocabulary

Status: Closed

## Goal

Introduce an IO-free pure reducer for Queue task lifecycle decisions so current
task behavior can be reproduced from explicit state, event, and context inputs.

## Scope

- Add a task lifecycle FSM module under `novaic-agent-runtime/queue_service`.
- Model task states currently represented by `tq_tasks.status`.
- Add table-driven tests for legal transitions, illegal transitions, retries,
  terminal failures, release, cancel, and stale recovery decisions.
- Add guard coverage that the reducer does not import clock, random, env, DB,
  files, or network boundaries.

## Out Of Scope

- Persisting task FSM state belongs to PR-305.
- Routing `TaskQueue` through the reducer belongs to PR-306.
- Deleting old task SQL branches belongs to PR-307.

## Small Tickets

- [x] **TASK-FSM-01 Vocabulary**: define states, events, actions, and payload
  keys.
- [x] **TASK-FSM-02 Reducer**: implement deterministic pure transition logic.
- [x] **TASK-FSM-03 Tests**: add table-driven transition and guard tests.
- [x] **TASK-FSM-04 Review**: run targeted tests and hidden-input scan.

## Explicit Dependency Boundary Review

Allowed explicit inputs:

- `FsmStateSnapshot`
- `FsmEvent`
- explicit context mapping with retry and stale policy values

Forbidden hidden inputs:

- clock/time
- UUID/random IDs
- environment variables
- DB/file/network reads
- mutable module globals

## Branch / Old Code Cleanup Ledger

Removed in this PR:

- None. This PR adds the reducer before cutover.

Must be removed by follow-up tickets:

- Direct task lifecycle mutation branches in `TaskQueue`: PR-307.

## Verification

- `pytest tests/test_pr304_task_lifecycle_fsm.py` — 15 passed.
- Hidden-input guard is included in
  `tests/test_pr304_task_lifecycle_fsm.py::test_task_lifecycle_fsm_has_no_hidden_io_inputs`.

## Closure Notes

Added `queue_service/task_fsm.py` with a pure task lifecycle reducer and
table-driven tests for publish, claim, complete, retry, terminal failure,
release, cancel, heartbeat timeout retry, heartbeat timeout terminal, invalid
transition rejection, deterministic replay, and hidden-input guard coverage.
No runtime cutover happened in this PR; PR-305/PR-306 own persistence and active
path routing.
