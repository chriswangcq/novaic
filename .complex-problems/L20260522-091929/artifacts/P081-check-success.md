# Saga Repository And Worker Lease Verified

## Summary

P081 is successful. Results `R081`, `R082`, `R083`, and parent result `R084` cover saga candidate query dialects, saga lifecycle mutation locking, JSONB handling, and worker lease ledger Postgres semantics.

## Evidence

- P090 / R081 wires saga claim/recovery/cancel candidate helpers with Postgres row locks, native heartbeat comparison, and JSONB context filtering.
- P091 / R082 wires `_get_saga_for_update` through `FOR UPDATE OF ss`, routes direct single-saga read paths through it, and fixes saga JSONB binding/row parsing.
- P092 / R083 validates worker lease adapter behavior over the Postgres-aware generic FSM store.
- Selected child verification passed across focused saga query, saga mutation, worker lease, generic FSM store, and existing saga/lease sqlite regression suites.

## Criteria Map

- Saga claim/recovery uses Postgres-safe selection and locking -> P090 / R081.
- Saga single-row lifecycle operations lock the relevant saga-state row -> P091 / R082.
- Saga stale recovery uses native timestamptz comparisons -> P090 / R081.
- Saga cancel/filter by agent uses JSONB context predicates -> P090 / R081.
- Worker lease event/state upserts preserve generation and unique semantics -> P092 / R083.
- Focused tests cover duplicate/loser shapes, stale recovery, cancel-by-agent, lease generation/state writes, and lease recovery-adjacent behavior -> P090/P091/P092 focused tests and selected regressions.

## Execution Map

- T084 split into P090, P091, and P092.
- R081 closed saga query dialect.
- R082 closed saga mutation locking and JSON handling.
- R083 closed worker lease ledger validation.
- R084 records the parent split result.

## Stress Test

- Failure mode: saga claim/recovery/cancel candidates race without row locks. Covered by `FOR UPDATE ... SKIP LOCKED` assertions.
- Failure mode: stale recovery still uses SQLite `datetime(...)`. Covered by native heartbeat SQL assertions.
- Failure mode: Postgres native saga JSONB values are lost during row parsing. Covered by native JSONB row tests.
- Failure mode: worker lease duplicate events throw or overwrite incorrectly. Covered by unique-violation fallback test.

## Residual Risk

- Live Postgres saga/lease contention validation remains a later Queue staging validation problem.
- Session/outbox and transient error guard slices remain separate P074 children.

## Result IDs

- R081
- R082
- R083
- R084
