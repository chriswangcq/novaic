# PR-320 Saga Projection Physical Schema Cut

Status: Closed
Owner: Codex
Phase: 8

## Goal

Physically remove saga lifecycle state from `tq_sagas` so saga lifecycle
authority exists only in `tq_saga_state`, `tq_saga_events`, and worker lease
state.

## Scope

- Remove saga lifecycle columns from the `tq_sagas` schema.
- Add missing user-visible lifecycle read-model fields to `tq_saga_state`.
- Update SagaRepository inserts, projection writes, and read paths to use an
  explicit joined read model.
- Preserve existing public saga dictionary shape.

## Deletion Scope

- Delete `tq_sagas.status`, `claimed_by`, `claimed_at`, `heartbeat_at`,
  `dag_task_count`, `step_results`, `error`, `updated_at`, and `completed_at`.
- Delete SQL updates that write lifecycle values to `tq_sagas`.
- Delete tests that mutate saga projection lifecycle columns as a shadow
  authority.

## Acceptance Criteria

- Fresh schema has no saga lifecycle columns on `tq_sagas`.
- `SagaRepository.claim`, `heartbeat`, `recover_stale`, `mark_launched`,
  `append_step_result`, `check_saga_complete`, `mark_completed`, `mark_failed`,
  `get_pending`, `cancel_all`, and `cancel_pending` continue to work through
  the joined read model.
- Saga lifecycle values are persisted in `tq_saga_state`.
- Tests prove `tq_sagas` cannot be used as saga lifecycle authority.

## Verification

- Phase 8 targeted tests: `45 passed`.
- Full `novaic-agent-runtime`: `451 passed`.
- `novaic-business`: `176 passed`.
- `novaic-common` with runtime contracts: `140 passed`.
- `python -m compileall -q queue_service`.
- `git diff --check`.

## Closure Notes

- Removed saga lifecycle columns from `tq_sagas`: status, claimed_by,
  claimed_at, heartbeat_at, dag_task_count, step_results, error, updated_at,
  and completed_at.
- Added claimed_at to `tq_saga_state`; existing state row now remains the only
  source for saga progress, step results, errors, heartbeat, and terminal
  timestamps.
- Updated SagaRepository to insert only immutable saga projection content into
  `tq_sagas` and read lifecycle fields through a joined read model from
  `tq_saga_state`.
- Removed the direct `UPDATE tq_sagas` projection writer path entirely.
- Added explicit saga heartbeat lifecycle events so heartbeat read-model state
  no longer depends on a projection-table column.
