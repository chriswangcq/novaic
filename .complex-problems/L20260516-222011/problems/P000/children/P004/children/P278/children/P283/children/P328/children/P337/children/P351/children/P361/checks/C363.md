# P361 source map check

## Summary

Success. R342 solves P361 by producing a concrete source map of normal finalization, saga failure compensation, failed-finalize suspected-dead recovery, recovery dispatch, and recovery archive publication. It also explicitly identifies ambiguous paths for downstream P362/P363 instead of treating them as safe.

## Evidence

- R342 cites production line ranges in:
  - `queue_service/saga_repo.py`
  - `queue_service/session_recovery.py`
  - `queue_service/session_outbox.py`
  - `queue_service/session_repo.py`
  - `queue_service/session_wake_plan.py`
  - `task_queue/contracts/react_think.py`
  - `task_queue/contracts/react_actions.py`
- R342 includes a table mapping each path to output, identity source, and risk.
- R342 lists representative tests that already cover compensation, suspected-dead recovery, recovery dispatch, and recovery archive publication.

## Criteria Map

- Inspect `queue_service/saga_repo.py`, `queue_service/session_recovery.py`, saga compensation code, and related tests: satisfied by R342 file/line evidence and test coverage map.
- Produce a concise source map of every path that creates or replays `wake_finalize` after failure/recovery: satisfied by the five-row source map table.
- Identify the source of `scope_id`, wake/root scope path, subagent id, and session generation for each path: satisfied by the identity source column and notes.
- Mark any ambiguous path as requiring a downstream child fix: satisfied by explicit gaps assigned to P362 and P363.

## Execution Map

- Read-only source searches found relevant production and test paths.
- Targeted file reads established the exact identity propagation behavior.
- R342 separated safe normal/recovery-dispatch paths from ambiguous compensation/recovery-archive paths.

## Stress Test

The source map was checked against the failure mode “a synthesized finalize task mutates without generation.” It found exactly the two risk surfaces expected from that stress test: compensation can create `wake_finalize` without requiring generation, and recovery archive publishes direct `cortex.scope_end` without generation.

## Residual Risk

- Non-blocking for P361: the two ambiguous paths are real implementation work, but they are already represented by sibling child problems P362 and P363 under P351.

## Result IDs

- R342
