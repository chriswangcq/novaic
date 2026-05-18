# PR-315 — Queue FSM Final Residue Guard

Status: Closed

## Goal

Close the durable FSM host migration by deleting or guarding old active
lifecycle paths.

## Scope

- Add static residue guards for task/saga/session lifecycle direct mutation.
- Update architecture docs and runbooks to the durable FSM host model.
- Remove old compatibility names, stale comments, and dual-path tests.
- Produce final code change statistics and branch cleanup notes.

## Explicit Dependency Boundary Review

Every lifecycle decision must be traceable to an explicit event and pure
reducer. Any exception must be documented as a projection write, not decision
logic.

## Branch / Old Code Cleanup Ledger

Removed in this PR:

- Task/Saga generation fallback to projection rows; missing FSM state now fails
  fast.
- Final unguarded residue surface for direct task/saga/session lifecycle table
  mutation, hidden reducer IO, and legacy/compatibility dual-path naming.
- Historical schema rewrite wording was removed from the active schema
  initializer and the matching fail-fast test assertion.

## Verification

- `pytest -q tests/test_pr315_queue_fsm_final_residue_guard.py`
- `pytest -q tests/test_pr244_remove_pending_triggers.py tests/test_pr314_queue_control_plane_audit_replay.py tests/test_pr315_queue_fsm_final_residue_guard.py`
- Full `novaic-agent-runtime` suite: `pytest -q` (`434 passed`)
- Full `novaic-business` suite: `pytest -q` (`176 passed`)
- Full `novaic-common` suite with runtime contracts:
  `PYTHONPATH=.:../novaic-agent-runtime pytest -q` (`140 passed`)
- Final residue grep for direct task/saga/session lifecycle mutation and old
  dual-path names.
- `git diff --check`

## Closure Notes

Closed. Added final static guard tests proving Queue reducers stay boundary-free,
task/saga direct SQL writes are projection-only, active Queue coordinators have
no legacy/compat/fallback/shadow lifecycle language, and generation must come
from FSM state rather than mutable projection rows.
