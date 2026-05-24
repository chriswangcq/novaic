# Implement persisted execution result model

## Problem

Release Controller must store `PlanExecutionResult` in the final `ReleaseRun` record while keeping old run records readable. This child handles the local code/model/state/API/test implementation.

## Success Criteria

- `PlanExecutionResult` is serializable/deserializable without circular imports.
- `ReleaseRun` stores optional `execution_result` and round-trips old/new JSON records.
- `execute_planned_release()` persists execution results on success, failure, and dry-run.
- Tests cover model serialization, state persistence, service/run endpoint visibility, poller persisted runs, and failure partial results.
- Local validation passes.
