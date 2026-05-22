# Port Durable Outbox Drain And Retry Semantics To Postgres

## Problem Definition

Session and saga outbox drainers currently list pending rows and then publish effects. Under Postgres, two drainers can otherwise read the same pending row before either marks it published or failed. Task/session/saga/lease outbox ledgers also need deterministic Postgres ordering and retry/dead-letter updates that preserve publish-before-ack replay semantics.

## Proposed Solution

Use transaction-scoped Postgres row claims rather than adding claim metadata in this slice:

1. Make generic FSM `list_pending_outbox(...)` use deterministic `created_at, id` ordering and `FOR UPDATE SKIP LOCKED` for Postgres, requiring an explicit transaction so locks remain held through publish and ack/failure updates.
2. Wrap session and saga outbox drain loops in explicit outbox-drain transactions with dedicated lock types. This makes selection, external publish, and published/failed marking one bounded publish-before-ack unit.
3. Keep SQLite behavior unchanged: SQLite continues to select pending rows in stable legacy order without `FOR UPDATE`.
4. Preserve success/failure transitions through the existing generic store methods: publish success is idempotent with `COALESCE(published_at/acked_at)`, and failure increments attempts and moves to `dead_letter` at the configured threshold.
5. Add focused Postgres tests for `FOR UPDATE SKIP LOCKED`, explicit-transaction enforcement, publish-before-ack retry SQL, dead-letter SQL, deterministic ordering, and drain-loop transaction guards.

## Acceptance Criteria

- Postgres pending outbox selection uses `FOR UPDATE SKIP LOCKED` inside an explicit transaction.
- Session and saga drainers keep selection, publish, and mark-published/failed inside a dedicated outbox-drain transaction.
- SQLite list/drain behavior remains compatible with existing tests and does not gain Postgres lock syntax.
- Publish success remains idempotent for replay after a crash between external publish and ack.
- Publish failure increments attempts and deterministically returns pending or dead-letters based on `max_attempts`.
- Tests cover duplicate-drainer protection SQL/guarding, deterministic ordering, publish-before-ack retry, and dead-letter transition.

## Verification Plan

- Add/extend focused Postgres FSM store tests.
- Add source or fake behavior tests for session and saga drainer transaction boundaries.
- Run generic FSM outbox tests, session/saga outbox cutover tests, queue Postgres boundary tests, and compile checks.

## Risks

- Holding a DB transaction while publishing external effects is deliberate for this first Postgres runtime but can increase lock duration. It is acceptable because the outbox row is the durable authority and retry is idempotent.
- Callers that list Postgres pending outbox rows outside a transaction should now fail fast; any such caller must either become a drainer transaction or remain SQLite/test-only.
- A later scaling pass may replace transaction-scoped locks with persisted claim owner/timeout metadata.

## Assumptions

- `FOR UPDATE SKIP LOCKED` plus a transaction covering publish and ack/failure is sufficient duplicate-drainer protection for the first Postgres runtime.
- Task and worker-lease outbox ledgers use the same generic FSM store semantics even if no active drainer is wired for them yet.
