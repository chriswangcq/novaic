# PR-233C — Dead Active Session Recovery and Structural Archive

| Field | Value |
| --- | --- |
| Status | `[x]` |
| Owner | Codex |
| Created | 2026-05-05 |
| Repos | `novaic-agent-runtime`, `novaic-cortex`, docs |
| Depends on | PR-233A, PR-233B |

## Objective

Make stuck active sessions recover explicitly instead of silently deleting the
Queue active-session row while Cortex still exposes an open child skill.

## Current-State Analysis

`SagaOrchestrator.mark_failed()` currently has a watchdog branch for failed
`wake_finalize` compensations. That branch removes `tq_active_sessions`, which
lets later IM dispatch create a new wake. However, Cortex may still have an
unclosed child skill, so the LLM prompt can show a stale active stack and
`skill_end` can fail with a stack mismatch.

## Implementation Scope

- Define an explicit dead-session snapshot / decision:
  - active row age / heartbeat
  - saga state
  - wake finalize state
  - Cortex stack state if available
- Add recovery semantics:
  - mark active session as recovery/dead before accepting new wake creation
  - migrate any active inbox or pending trigger into the recovery wake
  - force structural archive / close marker for dangling Cortex child scopes
- Ensure Queue does not treat dangling child skill as a healthy active wake.

## Expected Result

A failed or stale active wake becomes a recovery case with explicit evidence,
not an accidental "no active session" state.

## Implementation Result

- Added `tq_session_recoveries` schema table for explicit recovery evidence.
- `wake_finalize` failure now:
  - records the failed scope/saga/reason and force-archive metadata
  - clears the active session row
  - enqueues idempotent `cortex.scope_end` recovery archival
- `SessionRepository.dispatch()` consumes recovery markers into a new
  `trigger_type=recovered` wake.
- Orphan `tq_pending_triggers` are migrated into the recovery wake metadata so
  message ids are not lost.

## Verification

- Unit test for failed `wake_finalize` recovery path.
- Test pending input migration from dead session to recovery wake.
- Test dangling Cortex child skill produces a structural archive request or
  recovery marker.
- Smoke test reproducing the previous symptom: old wake fails, user sends
  "continue", new wake no longer inherits an impossible child-skill stack.

## Verification Result

- `test_wake_finalize_failure_creates_recovery_marker_and_archive_task`
- `test_recovery_wake_carries_unconsumed_inbox_inputs`
