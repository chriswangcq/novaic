# PR-273 — Session Harness Final Residue Guard

Status: Closed

## Goal

Add a final source-level residue guard for the Queue session harness and remove stale active-code wording that implies an old/current dual path.

## Why

After the FSM/ledger boundary migration, stale words and half-removed old-path hints become expensive: future humans and agents may infer that retired paths are still authoritative. The active harness should describe only the current path.

## Scope

- Remove misleading `legacy` wording from active session harness helper docs/tests.
- Add source guards for retired active-session, pending-trigger, direct-saga, state-record, and duplicated ledger-payload paths.
- Keep historical ticket docs unchanged unless they describe active behavior incorrectly.

## Non-Goals

- Do not rewrite historical tickets.
- Do not ban legitimate `SagaOrchestrator.create()` inside the outbox dispatcher imperative boundary.
- Do not rename public compatibility APIs outside the session harness.

## Acceptance Criteria

- Active session harness files no longer use stale `legacy` wording for current behavior.
- Guard test protects the current harness shape after PR-258 through PR-272.
- Full `novaic-agent-runtime` test suite passes.

## Verification

- `pytest tests/test_pr273_session_harness_final_residue_guard.py tests/test_pr263_session_pending_projection_boundary.py tests/test_pr271_session_attach_flow_consolidation.py tests/test_pr272_session_active_state_ledger_boundary.py`
- `pytest`
- `git diff --check`

## Closure Notes

- Removed stale `legacy` wording from active session projection docs/tests.
- Added `tests/test_pr273_session_harness_final_residue_guard.py` to pin the current harness boundary:
  - no retired active-code markers in session harness files,
  - no `SessionRepository` direct saga/event/state writes,
  - exactly one wake saga creation owner in `SessionOutboxDispatcher`,
  - one attach publication owner,
  - active state recording owned by `SessionLedgerRepository`.
- Targeted residue/boundary tests passed: 11 passed.
- Full `novaic-agent-runtime` test suite passed: 317 passed.
- `git diff --check` passed.
- Source residue scan only reports the expected pure FSM `session_finalize` event definition in `session_fsm.py`.
