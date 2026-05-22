# Port Saga Lifecycle Mutation Locking To Postgres

## Problem Definition

Saga lifecycle methods such as heartbeat, launch, step result append, completion, fail, and cancel read saga state before deciding transitions, but `_get_saga_for_update` does not use a Postgres row lock. Saga JSON fields also still have SQLite-era assumptions: create stores context as JSON text, and `_row_to_dict` can try to `json.loads` native Postgres JSONB dict values.

## Proposed Solution

Add backend-aware saga helpers in `queue_service/saga_repo.py`:

- `_saga_for_update_sql` with `FOR UPDATE OF ss` for Postgres and the existing select for sqlite.
- JSON value helpers so `create` binds context as native JSONB-compatible values in Postgres while preserving JSON text for sqlite.
- Row JSON normalization that decodes sqlite JSON strings and preserves native Postgres dict/list values for `context` and `step_results`.

Wire `_get_saga_for_update` through the helper so existing lifecycle methods that already call it gain explicit Postgres row locking. Add focused tests for lock SQL shape, no-op lifecycle paths using the lock query, JSONB context binding, native JSONB row parsing, and sqlite compatibility.

## Acceptance Criteria

- Postgres `_get_saga_for_update` locks the relevant saga-state row with `FOR UPDATE OF ss`.
- Heartbeat, mark-launched, mark-completed, mark-failed, cancel-pending, and direct pending cancel paths continue to read through `_get_saga_for_update` before decisions.
- Saga create binds context as a native JSONB-compatible value in Postgres and JSON text in sqlite.
- `_row_to_dict` preserves native dict/list values for Postgres `context` and `step_results` while still decoding sqlite JSON strings.
- Existing sqlite saga lifecycle tests remain compatible.

## Verification Plan

Add focused tests for `_saga_for_update_sql`, create JSON binding, `_row_to_dict` native JSONB handling, and no-op lifecycle methods on a fake Postgres DB that assert `FOR UPDATE OF ss` is used. Run those tests plus selected existing saga lifecycle/FSM tests, worker lease ledger tests, and Queue Postgres boundary/idempotency tests.

## Risks

- Some saga methods read state through custom joins instead of `_get_saga_for_update`; tests should identify any lifecycle paths that still bypass locking.
- Native JSONB row normalization must not break sqlite JSON string decoding.
- Real concurrent saga mutation behavior remains a later staging validation item.

## Assumptions

- P090 already handles claim/recovery/cancel candidate row locking.
- P079 generic FSM store already handles Postgres JSONB/timestamp state writes for saga FSM state tables.
