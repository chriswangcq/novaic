# Build Queue Postgres FSM Store Foundation

## Problem Definition

The generic Queue FSM store is currently named and implemented as SQLite-specific persistence. It serializes JSON to text, retries SQLite busy strings, commits standalone mutations, and uses `rowid` ordering in several event/outbox reads. The Postgres repository port needs a dialect-aware foundation so task, saga, lease, and session ledgers can share correct SQL generation instead of each re-implementing JSONB, ordering, conflict, and transaction behavior.

## Proposed Solution

Introduce a small Queue FSM dialect layer and a Postgres-capable store boundary while preserving existing sqlite fixtures. Separate the SQL/value differences for sqlite and postgres: JSON text versus native JSONB-friendly values, rowid ordering versus `(created_at, id)`, SQLite busy retries versus no SQLite retry in PG mode, and standalone mutation commit behavior versus explicit transaction requirements. Update ledger construction to choose the store/dialect from the database backend and add focused tests around generated SQL/value behavior without needing a real production database.

## Acceptance Criteria

- FSM store code has an explicit sqlite/postgres dialect boundary or separate Postgres store class.
- Postgres FSM SQL does not emit SQLite PRAGMAs, `rowid`, SQLite busy retry logic, or SQLite-only unique/busy exception matching.
- Event append, idempotent append, state upsert, outbox append, event listing, unconsumed-event listing, mark-consumed, pending-outbox listing, and outbox status updates have Postgres-safe SQL/value behavior.
- Postgres ordering uses deterministic `created_at, id` or `created_at DESC, id DESC` instead of `rowid`.
- Postgres path preserves JSON payload values as native JSON-compatible objects for JSONB binding while sqlite path preserves existing JSON text behavior.
- Focused tests cover the Postgres FSM store/dialect behavior and selected existing sqlite FSM tests still pass.

## Verification Plan

Run focused tests for the new FSM dialect/store plus existing FSM ledger tests such as task, saga, lease, session, generic FSM store, and transition runner tests. Include static assertions that the Postgres path does not emit `rowid`, SQLite busy retries, or SQLite-only exception classification.

## Risks

- Changing the existing sqlite store directly could break many session/task/saga fixtures; keep sqlite behavior covered and isolate PG behavior.
- A fake Postgres test can prove SQL/value generation but not row-lock runtime behavior; actual real-Postgres validation belongs to later staging.
- JSONB binding must avoid double-serializing payloads in the PG path while not changing sqlite behavior.

## Assumptions

- P073/P078 already provide the Queue Postgres database adapter and schema.
- Repository-specific row-lock claim/recovery logic will be handled in later P074 children after this foundation exists.
- The initial PG FSM store can be verified with fake DB/cursor tests before staging integration.
