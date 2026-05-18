# PR-255 Reliable Evolution FSM-08 Legacy Compat Cleanup

Status: `[x]` deployed and closed

## Goal

Remove or quarantine residue left after PR-251..PR-254 so future agents do not
revive old branches. In AI-era terms: code is cheap, stale branch surfaces are
expensive.

## Phase Ledger

```text
Phase: FSM-08 legacy cleanup
Subject: retired session harness branches and misleading docs/tests
Old source of truth: mixed legacy/shadow/current references
New source of truth: session_state + append-only inbox + durable outbox + pure FSM + finalize events
Input events: unchanged
Decision function: pure FSM only
State transition: FSM-owned
Outbox effects: live retryable effects only; observe effects historical
Observation events: retained only where useful diagnostics remain
Generation/idempotency key: explicit generation everywhere
Shadow drift metric: retired
Cutover switch: remove stale dual-route flags
Rollback path: revert PR-255
Legacy deletion condition: PR-251..PR-254 closed and deployed
Tests: residue scans for retired terms and direct side-effect paths
Docs/guards to update: roadmap archaeology banners, tests names
```

## Small Tickets

- [x] **FSM-08-A Code residue scan**: remove unused compat/fallback branches
  from runtime session harness.
- [x] **FSM-08-B Test naming cleanup**: rename tests that describe old shadow
  behavior as current behavior.
- [x] **FSM-08-C Docs cleanup**: add archive banners or delete stale roadmap
  fragments that look actionable.
- [x] **FSM-08-D Guard tests**: add residue scans for direct publish/create and
  missing generation/finalize reason.

## Explicit Dependency Boundary Review

Cleanup must not replace explicit dependencies with fallback behavior. If old
hidden behavior is not a product requirement, remove it and guard it.

## Verification

- `rg` residue scans listed in this ticket's review result.
- `pytest -q`
- `git diff --check`

## Review Result

Local pass:

- Deleted `queue_service/session_decisions.py`; dispatch decision helpers now
  live in the pure `session_fsm` module.
- Retired dispatch drift trace keys (`legacy_action`, `shadow_action`,
  `shadow_legacy_action`, `drift`) and pending projection drift payload fields.
  Diagnostics now record `result_action`, `fsm_action`, and `reason`.
- Removed the no-generation attach compatibility path: `session.attach_input`
  requires `expected_wake_scope_id` and `expected_session_generation`, and the
  session outbox refuses attach payloads missing generation.
- Renamed current tests away from old shadow/observe-only wording and updated
  docs/comments that described `tq_session_state` as future/shadow state.
- Added `tests/test_pr255_legacy_compat_cleanup.py` residue guards.

Verification run:

- `python -m py_compile queue_service/session_repo.py queue_service/session_fsm.py queue_service/session_outbox.py task_queue/handlers/runtime_handlers.py`
- `pytest tests/test_pr233_active_inbox_dispatch.py tests/test_pr236_session_fsm_decision.py tests/test_pr238_generation_checked_attach.py tests/test_pr248_attach_outbox_cutover.py tests/test_pr253_dispatch_pure_fsm_cutover.py tests/test_pr255_legacy_compat_cleanup.py -q`
- `pytest tests/test_pr153_pending_inbox_metadata.py tests/test_pr233_active_inbox_dispatch.py tests/test_pr235_session_ledger.py tests/test_pr236_session_fsm_decision.py tests/test_pr237_session_outbox_observe.py tests/test_pr238_generation_checked_attach.py tests/test_pr239_append_only_inbox.py tests/test_pr240_input_consumption.py tests/test_pr241_pending_inbox_projection.py tests/test_pr243_inbox_restart_cutover.py tests/test_pr245_suspected_dead_recovery.py tests/test_pr247_recovery_outbox_cutover.py tests/test_pr248_attach_outbox_cutover.py tests/test_pr249_observed_wake_outbox_cleanup.py tests/test_pr250_observed_wake_effect_rename.py tests/test_pr251_wake_creation_outbox_cutover.py tests/test_pr252_session_state_ssot.py tests/test_pr253_dispatch_pure_fsm_cutover.py tests/test_pr254_finalize_ownership.py tests/test_pr255_legacy_compat_cleanup.py tests/test_pr48_turn_finalizer.py tests/test_finalize_summary_boundary.py tests/test_pr234_repeated_scope_mismatch.py -q`

Full suite passes locally.

Deployment closure:

- `./deploy runtime` completed successfully on 2026-05-06.
- `./deploy status` showed api services online on ports 19900, 19999, 19998,
  19993, 19997, 19995, and 19996, with 8 worker processes and relay active.

## Rollback

Revert PR-255 only; do not rollback PR-251..PR-254 unless their own acceptance
criteria fail.
