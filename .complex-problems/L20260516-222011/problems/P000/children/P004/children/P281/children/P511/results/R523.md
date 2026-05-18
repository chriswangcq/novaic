# P511 Queue FSM Focused Test Execution Result

## Summary

Completed Queue FSM focused test execution across the three split verification groups.

## Child Results

- P517 (`R509`, `R513`, `R514`, `C547`): session/outbox/finalize focused group.
  - Final full subset rerun: 52 files, 247 tests, `247 passed in 1.37s`.
- P518 (`R518`, `C551`): task/saga/worker focused group.
  - Final corrected run: 26 files, 124 tests, `124 passed in 0.98s`.
- P519 (`R522`, `C555`): unit/tool-output/task_queue boundary group.
  - Final run: 12 files, 47 tests, `47 passed in 0.19s`.

## Total Focused Coverage Executed

- Focused target files across final groups: 90 file-target entries.
- Tests collected across final successful runs: 418.
- All final group runs exited with code 0.

## Notable Findings

- P517 initially failed in three tests; those were repaired as stale/incorrect expectations and then the full P517 subset reran green.
- P518 initially failed when run from the repository root because some tests rely on `novaic-agent-runtime` as cwd. The corrected runtime-cwd run passed.
- P519 ran cleanly from `novaic-agent-runtime`.

## Files Changed

Test expectation updates from P517 repair:

- `novaic-agent-runtime/tests/test_pr233_active_inbox_dispatch.py`
- `novaic-agent-runtime/tests/test_pr237_session_outbox_observe.py`
- `novaic-agent-runtime/tests/test_pr281_session_outbox_wrapper_boundary.py`

Ledger evidence artifacts were added under `.complex-problems/L20260516-222011/tmp/`.

## Residual Risk

P511 is focused verification, not a full repository-wide test suite. P512 static residue classification remains separate.
