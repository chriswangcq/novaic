# Persist Release Controller PlanExecutionResult in run records

## Problem

Release Controller currently returns `PlanExecutionResult` in the immediate trigger/promotion/rollback HTTP response, but the persisted `ReleaseRun` record only stores the command plan and final status/failure. After the request completes, `/v1/runs/{run_id}` and `/v1/status` cannot show per-step exit codes, skipped flags, stdout, or stderr. This weakens CI/CD auditability, especially for quality-gate runs.

## Success Criteria

- `ReleaseRun` persists a serialized `PlanExecutionResult` for completed runs.
- Stored run JSON round-trips existing and new run records without breaking old records that lack execution results.
- `/v1/runs/{run_id}`, `/v1/runs`, and `/v1/status` include the persisted execution result for new runs.
- Failed runs persist the partial execution result up to the failed step.
- Dry-run runs persist skipped execution results.
- Tests cover serialization, state round-trip, service response, poller persistence, and failure persistence.
- The change is deployed to the API-host Release Controller and verified with a dry-run or safe run.
