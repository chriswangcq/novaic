# Check: Session And Outbox Postgres Semantics Succeed

## Summary

`P082` is solved by `R089` plus follow-up `R090`. Session dispatch/attach/finalize now has explicit Postgres state-row locking and behavioral coverage; session rebuild/read-model SQL has deterministic Postgres ordering and row locks; durable outbox drains claim rows with `FOR UPDATE SKIP LOCKED` inside Postgres transactions; and Queue runtime no longer silently defaults to SQLite.

## Evidence

- P093/C092: session state locking and no-input-loss behavioral coverage succeeded.
- P094/C093: durable outbox drain/retry semantics succeeded.
- P095/C094: session/outbox SQLite runtime residue isolation succeeded.
- P097/C096: session rebuild/read-model Postgres SQL and lock semantics succeeded.
- Related verification runs include 113 queue/session/outbox/Postgres tests, 110 outbox/session/saga tests, 66 session locking tests, and 42 rebuild/read-model tests passing.

## Criteria Map

- Session first-dispatch/attach/finalize ensures and locks `tq_session_state(session_key)`: satisfied by P093/R085/R086/C092.
- Session rebuild/read models use Postgres-safe SQL and deterministic ordering: satisfied by P097/R090/C096.
- Outbox drain paths claim rows before external publish or enforce a constraint: satisfied by P094/R087/C093 using explicit transaction plus `FOR UPDATE SKIP LOCKED`.
- Pending/dead-letter outbox status transitions preserve retry semantics: satisfied by P094 SQL tests and existing outbox retry/dead-letter regressions.
- No-input-loss and at-most-one-active-session semantics covered by focused Postgres-path tests: satisfied by P093 behavioral tests and existing session SSOT regressions.
- Tests cover first-dispatch races, attach/finalize behavior, publish-before-ack retry, and deterministic ordering: satisfied across P093, P094, and P097.

## Execution Map

- R089 summarized the closed split children P093, P094, and P095.
- R090 closed the check-time rebuild/read-model follow-up P097.

## Stress Test

- Deterministic Postgres-mode fakes simulate session race/revalidation failure modes.
- Store-level tests assert Postgres row-lock SQL for session state and outbox drains.
- Rebuild SQL tests assert deterministic ordering and `FOR UPDATE OF ss SKIP LOCKED`.

## Residual Risk

- Live multi-process Postgres stress tests were not added; deterministic SQL/adapter/fake tests cover the intended correctness boundaries for this cutover.
- Future scaling may replace transaction-scoped outbox row locks with persisted claim owner/timeout metadata.

## Result IDs

- R089
- R090
