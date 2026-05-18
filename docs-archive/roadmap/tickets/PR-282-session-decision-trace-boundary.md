# PR-282 — Session Decision Trace Boundary

Status: Closed

## Goal

Move deterministic session dispatch decision trace construction from
`SessionRepository` to `session_fsm`.

## Scope

- Add a pure trace helper next to `decide_session_dispatch`.
- Replace repository-local trace helper calls.
- Delete repository-local `_session_dispatch_decision_trace`.

## Acceptance Criteria

- `session_repo.py` contains no `_session_dispatch_decision_trace` definition.
- Trace output remains stable.
- Targeted trace tests pass.
- Full runtime suite passes.

## Verification

- Targeted PR-282 test.
- `pytest`
- `git diff --check`

## Closure Notes

- Added `build_session_dispatch_decision_trace` to `session_fsm`.
- Replaced repository-local trace construction with the pure FSM helper.
- Deleted repository-local `_session_dispatch_decision_trace`.
- Added `tests/test_pr282_session_decision_trace_boundary.py`.
- Targeted FSM/trace/residue tests passed: 10 passed.
