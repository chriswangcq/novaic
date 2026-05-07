# PR-314 — Queue Control Plane Audit Replay

Status: Closed

## Goal

Add read-only audit/replay tooling for Queue Service FSM machines so state can
be explained from append-only events.

## Scope

- Add a diagnostic helper for session/task/saga/lease event streams.
- Summarize events, decisions, effects, observations, and final state.
- Keep the helper read-only and deterministic.

## Explicit Dependency Boundary Review

The audit helper may read DB/files as an explicit diagnostic boundary. It must
not mutate state or publish side effects.

## Branch / Old Code Cleanup Ledger

Removed in this PR:

- None directly.

Must be removed by follow-up:

- Any legacy runbook that asks operators to infer lifecycle from mutable status
  rows alone.

## Verification

- `pytest -q tests/test_pr314_queue_control_plane_audit_replay.py`
- `pytest -q tests/test_pr314_queue_control_plane_audit_replay.py tests/test_pr315_queue_fsm_final_residue_guard.py tests/test_pr313_worker_lease_fsm.py tests/test_pr313_worker_lease_ledger.py tests/test_pr313_worker_lease_cutover.py`
- Full `novaic-agent-runtime` suite: `pytest -q` (`434 passed`)
- `git diff --check`

## Closure Notes

Closed. Added `queue_service.queue_audit.build_queue_fsm_audit_report(...)`
for deterministic read-only audit summaries over session/task/saga/lease event
streams, final state, and outbox effects. Tests cover fixed event streams,
session decision-trace payload shape, and real Task/Saga/Lease ledger reads from
a local Queue DB fixture without mutation.
