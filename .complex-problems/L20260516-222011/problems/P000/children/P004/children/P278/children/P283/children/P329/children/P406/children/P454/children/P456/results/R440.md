# T447 Result: Runtime focused compatibility behavior tests

## Summary

Runtime focused compatibility behavior tests passed. The suite covers generation-checked attach, outbox cutover, finalize ownership, session-ended/environment notification paths, suspected-dead recovery, session-state SSOT, active-session removal, legacy compatibility cleanup, explicit runtime contracts, historical tool image guard, and shell output contract.

## Evidence

- Log: `.complex-problems/L20260516-222011/tmp/p456/runtime-focused-tests.log`
- Exit file: `.complex-problems/L20260516-222011/tmp/p456/runtime-focused-tests.exit`
- Exit status: `0`
- Pytest summary: `100 passed in 0.59s`

## Command

```bash
cd novaic-agent-runtime && PYTHONPATH=.:../novaic-common pytest -q \
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

## Changes

No source changes were made by this ticket. It only reran and saved focused runtime verification.

## Notes

The first wrapper attempt exposed a local zsh-script bug in my test harness (`status` is readonly, then an internal `exit` prevented the exit file from being written). I reran the same test command with a corrected wrapper and verified both log and exit file are present.
