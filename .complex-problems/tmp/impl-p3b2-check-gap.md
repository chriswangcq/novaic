# Phase 3B2 Check Not Successful

## Summary

R015 implements the active-stack projection write path and passes broad Cortex tests, but the verification evidence is not strict enough for the original P023 success criteria. The ticket explicitly asks for nested begin/end projection state and restart-like store reuse; current evidence covers helper-level nested frames and API-level single child begin/end, but not one end-to-end nested API lifecycle with a reopened SQLite store.

## Blocking Gaps

- Missing an API lifecycle test that opens nested skills, verifies the top-first SQLite stack after each push, closes the inner skill, and verifies the popped stack keeps the outer skill and wake.
- Missing a restart-like assertion that reads the persisted active-stack projection through a new operational SQLite store instance pointed at the same database file.
- These are verification gaps, not known production regressions. The implementation path is likely correct, but the check should not call P023 solved until those criteria are directly proven.

## Result IDs

- R015
