# PR-319 Task Projection Physical Schema Cut

Status: Closed
Owner: Codex
Phase: 8

## Goal

Physically remove task lifecycle state from `tq_tasks` so task lifecycle
authority exists only in `tq_task_state`, `tq_task_events`, and worker lease
state.

## Scope

- Remove task lifecycle columns from the `tq_tasks` schema.
- Move user-visible lifecycle read-model fields to `tq_task_state`.
- Update TaskQueue inserts, projection writes, and read paths to use an
  explicit joined read model.
- Preserve existing public `get_task` / `claim` dictionary shape.

## Deletion Scope

- Delete `tq_tasks.status`, `claimed_by`, `claimed_at`, `heartbeat_at`,
  `retry_count`, `max_retries`, `next_retry_at`, `error`, `started_at`,
  `finished_at`, and `version`.
- Delete SQL updates that write lifecycle values to `tq_tasks`.
- Delete tests that mutate task projection lifecycle columns as a shadow
  authority.

## Acceptance Criteria

- Fresh schema has no task lifecycle columns on `tq_tasks`.
- `TaskQueue.claim`, `complete`, `fail`, `heartbeat`, `recover_stale`,
  `release_task`, `cancel_all`, `get_task`, and idempotency lookup continue to
  work through the joined read model.
- Task lifecycle values are persisted in `tq_task_state`.
- Tests prove `tq_tasks` cannot be used as task lifecycle authority.

## Verification

- Phase 8 targeted tests: `45 passed`.
- Full `novaic-agent-runtime`: `451 passed`.
- `novaic-business`: `176 passed`.
- `novaic-common` with runtime contracts: `140 passed`.
- `python -m compileall -q queue_service`.
- `git diff --check`.

## Closure Notes

- Removed task lifecycle columns from `tq_tasks`: status, claimed_by,
  claimed_at, heartbeat_at, retry_count, max_retries, next_retry_at, error,
  started_at, finished_at, and version.
- Added claimed_at, error, started_at, and finished_at to `tq_task_state`.
- Updated TaskQueue to insert only projection content into `tq_tasks` and read
  lifecycle fields through a joined read model from `tq_task_state`.
- Kept `tq_tasks.result` as the only mutable task projection field.
- Added explicit task heartbeat lifecycle events so heartbeat read-model state
  no longer depends on a projection-table column.
