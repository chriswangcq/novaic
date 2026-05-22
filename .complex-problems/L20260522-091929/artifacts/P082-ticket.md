# Port Session And Outbox Semantics To Postgres

## Problem Definition

Session coordination and durable outbox delivery still carry SQLite-era assumptions: process-local serialization, SQLite-specific ordering and JSON handling, and pending outbox scans that do not claim rows before external publish. Under Postgres those assumptions can break no-input-loss, at-most-one-active-session, and publish-before-ack retry semantics when multiple workers or transactions touch the same session or outbox table.

## Proposed Solution

Port the session and outbox slice as explicit Postgres semantics rather than a hidden SQLite compatibility path.

1. Make `tq_session_state(session_key)` the serialization boundary for session dispatch, attach, finalize, and restart decisions. Brand-new sessions must first ensure a state row, then lock or compare-update it before any decision that depends on active session state.
2. Move session read/rebuild SQL through backend-aware helpers so Postgres uses deterministic `created_at, id` ordering, native JSONB payloads, and row/advisory locking where needed for startup rebuild.
3. Give durable outbox drains a Postgres-safe claim story. Prefer database-level claims with `FOR UPDATE SKIP LOCKED` and owner/timeout metadata if the schema already supports it; otherwise document and enforce a single-drainer runtime constraint for this first Postgres cutover.
4. Preserve publish-before-ack retry semantics: external publish happens only after the transition that wrote the outbox row is committed, and success/failure updates must leave rows retryable or dead-lettered deterministically under Postgres transactions.
5. Add focused Postgres-path tests around the concurrency and ordering contracts instead of maintaining a broad SQLite fallback behavior matrix.

## Acceptance Criteria

- Session first dispatch ensures and locks `tq_session_state(session_key)` or uses an equivalent explicit compare/update pattern before active-session decisions.
- Attach and finalize paths revalidate state under the same session serialization boundary and keep unconsumed inputs durable when they cannot attach.
- Session rebuild/read-model paths use Postgres-safe SQL, native JSON handling, and deterministic ordering.
- Outbox drain behavior either claims rows before publish under Postgres or has an explicit, tested single-drainer guard for the initial deployment.
- Pending, published, failed, and dead-letter outbox transitions preserve retry semantics after publish success/failure and process restart.
- Focused tests cover first-dispatch races, attach/finalize revalidation, no-input-loss, deterministic ordering, and publish-before-ack retry behavior.
- Old SQLite-specific paths are isolated to the SQLite adapter; queue service business logic does not branch on stale local `.db` paths.

## Verification Plan

- Add focused tests using Postgres SQL render/spy adapters for session locking and outbox claim/update semantics.
- Run the new session/outbox Postgres tests plus existing session repository, session ledger, generic FSM outbox, saga outbox, and queue Postgres boundary regressions.
- Run compile checks for `queue_service` modules touched by the port.
- Inspect diffs for residual SQLite-only SQL, local database path assumptions, and hidden fallback branches in session/outbox business logic.

## Risks

- Adding claim metadata may require schema changes and migration handling; if avoided for this cutover, the single-drainer constraint must be explicit and hard to misconfigure.
- Session finalization and dispatch can lose inputs if locking is applied after input consumption decisions rather than before them.
- Rebuild can race live dispatch if startup ordering or advisory locking is not made explicit.
- Over-generalizing the store API could keep SQLite fallback logic alive in business code instead of isolating dialect behavior in adapters.

## Assumptions

- The first Postgres runtime can tolerate a single outbox drainer per effect/table if schema claim metadata is deferred.
- SQLite support may remain only as a bounded test/development adapter during the transition, not as an equal production fallback path.
- Existing session ledger and FSM store abstractions are acceptable extension points as long as dialect-specific SQL stays behind explicit helper boundaries.
