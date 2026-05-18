# Run Task Saga Worker Focused Pytest

## Problem

Run pytest for the validated P518 task/saga/worker focused target list and capture exact execution evidence.

## Success Criteria

- Pytest is run from `novaic-agent-runtime` using the validated P518 target list.
- The log, exit code, and pass/fail summary are recorded.
- Empty-suite and partial-run false positives are rejected.
- Failures are preserved for follow-up instead of hidden.
