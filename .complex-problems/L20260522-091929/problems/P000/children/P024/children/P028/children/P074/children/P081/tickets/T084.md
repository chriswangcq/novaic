# Port Saga Repository And Worker Lease Semantics To Postgres

## Problem Definition

`queue_service/saga_repo.py` still has SQLite-shaped saga claim/recovery/cancel behavior: local busy-timeout hints, `datetime(...)` heartbeat comparisons, tuple-style assumptions, and `json_extract` context filtering. Saga lifecycle mutations and worker lease state/event writes need explicit Postgres row-lock or compare/update semantics without breaking existing sqlite fixtures.

## Proposed Solution

Split the work into smaller repository slices before execution:

- Saga candidate query dialects for claim, stale recovery, and cancel-by-agent.
- Saga single-row lifecycle mutation locking for heartbeat, launch, step result append, completion, fail, and cancel paths.
- Worker lease ledger Postgres compatibility for event/state/outbox writes, generation preservation, and unique state semantics.

Each slice should add focused fake Postgres tests for SQL shape and row/value binding, while selected existing saga/lease sqlite tests continue to pass.

## Acceptance Criteria

- Saga claim uses Postgres-safe candidate selection with stable ordering and `FOR UPDATE SKIP LOCKED` or an equivalent compare/update pattern.
- Saga stale recovery uses native timestamptz heartbeat comparison without SQLite `datetime(...)`.
- Saga cancel/filter by agent uses JSONB context predicates instead of `json_extract`.
- Saga single-row lifecycle operations lock or compare/update the relevant `tq_saga_state` row before decisions.
- Worker lease event/state/outbox writes remain compatible with Postgres JSONB/timestamptz values and preserve generation and unique state semantics.
- Focused tests cover duplicate saga claim losers, stale recovery, cancel-by-agent, lifecycle no-op/loser paths, and worker lease state/event writes.

## Verification Plan

Run new saga/lease Postgres dialect and mutation tests, selected existing saga FSM store and worker lease ledger tests, and the current Queue Postgres boundary/idempotency regression set. Use SQL shape assertions to prove Postgres paths avoid `datetime(...)`, `json_extract`, and SQLite-only row selection.

## Risks

- Saga repository methods cover multiple lifecycle paths and can easily hide independent correctness gaps.
- Worker lease ledger uses the shared generic FSM store, so changes may belong in shared store code rather than saga-only code.
- Fake Postgres tests prove dialect/row binding but live contention still belongs to staging validation.

## Assumptions

- P079 already made the generic FSM store Postgres-aware for JSON, ordering, and transaction boundaries.
- Queue Postgres schema already includes saga and worker lease tables with JSONB/timestamptz-compatible columns.
- Session/outbox and transient error guard work remain separate P074 children.
