# P360 success check

## Summary

Success. R337 satisfies the aggregate verification problem: tests and source guards cover the full terminal subagent finalize status path, and the remaining recovery/compensation boundary is explicitly recorded as outside P354.

## Evidence

- Aggregate pytest from R337 passed 109 tests across payload, handler, finalize ownership, scope-end, runtime contract, and DAG integration suites.
- Source guards found no live `last_scope_id` or `last_scope_archived_at` in touched runtime files.
- Source guards found no session-generation defaulting residue in touched runtime files.
- Mutation scan found terminal subagent `entity_update()` calls only in `task_queue/handlers/subagent_handlers.py`.
- `task_queue/handlers/subagent_handlers.py:85` validates sleeping identity before Business mutation.
- `task_queue/handlers/subagent_handlers.py:130` validates completed identity before Business mutation.
- Manual DAG inspection showed terminal status tasks depend on `session_ended`.

## Criteria Map

- Run focused tests covering wake_finalize payloads, subagent handlers, task path contracts, finalize ownership, and saga DAG integration: met by 109-test aggregate suite.
- Run source guards for last-scope residue, generation defaulting, and missing-generation compatibility: met by R337 source guard evidence.
- Verify no direct Business status mutation bypasses the new identity contract: met by mutation scan and handler line evidence.
- Record residual risks, especially recovery/compensation delegated to P351: met in R337 Known Gaps.

## Execution Map

- Verification-only ticket T345 produced R337.
- Commands run:
  - py_compile over touched runtime modules.
  - 109-test aggregate pytest suite.
  - source guard `rg` scans.
  - mutation-path `rg` scan.
  - manual DAG spec print.

## Stress Test

- Plausible failure mode: one of the previous child fixes lands but a separate direct terminal status write path remains and bypasses identity checks. The mutation scan found the terminal writes only in the guarded handlers; `set_awake` was identified as non-terminal and intentionally outside this contract.

## Residual Risk

- Recovery/compensation identity remains with P351. This does not block P360 because P360 is scoped to P354's terminal subagent status path.

## Result IDs

- R337
