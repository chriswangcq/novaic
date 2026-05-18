# Ticket: Run runtime focused compatibility behavior tests

## Problem Definition

The runtime side of P454 must prove the live Queue/session harness behavior still satisfies the FSM, generation, finalize ownership, recovery, and shell-output contracts after cleanup.

## Proposed Solution

Run this focused runtime test suite from `novaic-agent-runtime`:

```bash
PYTHONPATH=.:../novaic-common pytest -q \
  tests/test_pr238_generation_checked_attach.py \
  tests/test_pr248_attach_outbox_cutover.py \
  tests/test_pr254_finalize_ownership.py \
  tests/test_scope_end_environment_notifications.py \
  tests/test_finalize_summary_boundary.py \
  tests/test_pr245_suspected_dead_recovery.py \
  tests/test_pr247_recovery_outbox_cutover.py \
  tests/test_pr252_session_state_ssot.py \
  tests/test_pr257_remove_active_sessions_table.py \
  tests/test_pr255_legacy_compat_cleanup.py \
  tests/test_pr273_session_harness_final_residue_guard.py \
  tests/test_pr315_queue_fsm_final_residue_guard.py \
  tests/test_runtime_explicit_contracts.py \
  tests/unit/task_queue/test_no_historical_tool_image_injection.py \
  tests/unit/task_queue/test_shell_output_contract.py
```

Save stdout/stderr and exit status under `.complex-problems/L20260516-222011/tmp/p456/`.

## Acceptance Criteria

- Test command and log are saved.
- Exit status is 0.
- Log summary shows all selected tests pass.
- Any failure is not papered over; it becomes a follow-up repair problem.

## Verification Plan

- Inspect saved log tail and pytest summary.
- Record result only after the suite completes.
