# Map Queue SQLite FSM and Outbox Semantics to Postgres

## Problem Definition

`queue.db` is the largest and riskiest remaining SQLite state owner. It contains task, saga, session, worker-lease, outbox, idempotency, and configuration state. The service code uses SQLite-specific behavior such as WAL, busy retries, `INSERT OR IGNORE`, conflict handling, JSON expressions, transaction boundaries, and local lock assumptions.

Before any queue runtime migration or cutover, these semantics must be mapped to Postgres primitives with enough detail that an implementation ticket cannot accidentally change queue correctness.

## Proposed Solution

Inspect the production `queue.db` schema and row counts, inspect queue service code paths, then produce a durable migration map that covers:

1. Table-by-table Postgres schema strategy.
2. Transaction boundaries for task/saga/session transitions.
3. Claim/recovery semantics using row locks, `FOR UPDATE SKIP LOCKED`, uniqueness, and advisory locks where appropriate.
4. Outbox and idempotency replay guarantees.
5. JSON field handling with JSONB and indexes.
6. Required migration/cutover phases and verification checks.
7. Explicit no-go rules for unsafe table-copy cutover.

The output should be a plan/mapping artifact only. No production queue data should be migrated or mutated in this ticket.

## Acceptance Criteria

- Current queue tables, row counts, and table groups are documented from production evidence.
- Queue code paths that own tasks, sagas, sessions, worker leases, outboxes, idempotency, and recovery are identified.
- SQLite-specific SQL/locking/busy behavior is mapped to concrete Postgres behavior.
- Each queue table group has a Postgres schema/index/constraint strategy.
- Outbox, idempotency, and lease correctness invariants are stated.
- A phased implementation/cutover plan and verification matrix exists.
- The production queue remains on SQLite and healthy after this ticket.

## Verification Plan

Use `sqlite3` on the production `queue.db` for schema and counts, use `rg` and focused file reads for queue code paths, write the mapping artifact locally and to the `api` host, and verify the queue health endpoint after read-only inspection. Confirm no migration or data mutation was attempted.

## Risks

- Missing a SQLite-specific behavior can produce duplicate task claims, lost outbox effects, stuck leases, or broken recovery.
- SQLite and Postgres JSON semantics differ; indexes and operators must be explicit.
- `FOR UPDATE SKIP LOCKED` is powerful but can hide starvation if not paired with ordering and retry policy.
- A table-copy migration without service quiescence can miss in-flight state.

## Assumptions

- Queue runtime stays on SQLite during this mapping ticket.
- Future implementation can remove SQLite fallback once Postgres cutover succeeds.
- The source tree in this workspace is representative of the code deployed on `api`.
