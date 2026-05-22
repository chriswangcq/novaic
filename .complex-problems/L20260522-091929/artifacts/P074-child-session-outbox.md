# Port Session And Outbox Semantics To Postgres

## Problem

Session dispatch/finalize/rebuild and task/saga/session/lease outbox paths must preserve no-input-loss, at-most-one-active-session, and publish-before-ack retry semantics under Postgres. Current code was built around SQLite store behavior and process-local locking; the Postgres path needs explicit row locking, deterministic ordering, and outbox claim semantics. This belongs under P074 because session coordination and outbox delivery are correctness-critical but separable from task/saga repository ports.

## Success Criteria

- Session first-dispatch/attach/finalize ensures and locks `tq_session_state(session_key)` or uses an equivalent explicit compare-and-update pattern.
- Session rebuild and read models operate on Postgres-safe SQL and deterministic ordering.
- Outbox drain paths claim rows before external publish or document/enforce a single-worker constraint for the first Postgres runtime.
- Pending/dead-letter outbox status transitions preserve retry semantics under Postgres transactions.
- No-input-loss and at-most-one-active-session semantics are covered by focused tests in the Postgres path.
- Tests cover session first-dispatch races, attach/finalize behavior, outbox publish-before-ack retry, and deterministic outbox ordering.
