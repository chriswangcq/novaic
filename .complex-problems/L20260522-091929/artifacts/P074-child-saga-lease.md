# Port Saga Repository And Worker Lease Semantics To Postgres

## Problem

`queue_service/saga_repo.py` and worker lease ledgers still rely on SQLite transaction behavior, local busy-timeout hints, `datetime(...)`, and JSON extraction. Saga create/claim/heartbeat/recover/launch/complete/fail/cancel and worker lease state/event writes must be ported to explicit Postgres row-lock or compare-and-update semantics. This belongs under P074 because saga concurrency and worker lease ownership are independent correctness paths from task and session handling.

## Success Criteria

- Saga claim/recovery uses Postgres-safe row selection and locking, including `FOR UPDATE SKIP LOCKED` or a reviewed compare-and-update pattern.
- Saga single-row lifecycle operations lock or compare/update the relevant saga state rows explicitly.
- Saga stale recovery uses native timestamptz comparisons rather than SQLite `datetime(...)`.
- Saga cancel/filter by agent uses JSONB context predicates rather than `json_extract`.
- Worker lease event/state upserts preserve generation and unique `(machine_type, machine_id)` semantics under Postgres.
- Focused tests cover duplicate saga claim losers, stale recovery, saga cancel-by-agent, lease generation/state writes, and lease recovery behavior.
