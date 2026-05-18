# Hidden input remediation tests and guards not-success check

## Summary

P474 is not successful yet. Guard evidence is good, but the focused pytest suite failed because part of the suite was invoked from the wrong working directory.

## Blocking Gaps

- `hidden-input-focused-tests.exit` is `1`; four `test_pr273_session_harness_final_residue_guard.py` tests failed with `FileNotFoundError`.
- The failure mode is command invocation/cwd, not the hidden-input implementation itself, but it still blocks verification.

## Result IDs

- R462
