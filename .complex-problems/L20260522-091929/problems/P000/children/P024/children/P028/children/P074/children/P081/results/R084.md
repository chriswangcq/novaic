# Saga Repository And Worker Lease Semantics Ported

## Summary

Completed the P081 saga and worker lease repository slice through three child problems:

- P090 / R081: saga claim/recovery/cancel candidate query dialect.
- P091 / R082: saga lifecycle mutation locking and JSONB handling.
- P092 / R083: worker lease ledger Postgres semantics validation.

Together these cover saga candidate row locking, native timestamptz recovery comparisons, JSONB cancel-by-agent filtering, saga-state row locking for single-row lifecycle decisions, native JSONB-compatible saga context/step result handling, and worker lease event/state/outbox Postgres binding semantics.

## Done

- Saga claim candidates use stable ordering and `FOR UPDATE OF ss SKIP LOCKED` in Postgres mode.
- Saga stale recovery uses native heartbeat comparison and `FOR UPDATE OF ss, ls SKIP LOCKED`.
- Saga cancel-by-agent uses `ss.context ->> 'agent_id' = ?`.
- Saga `_get_saga_for_update` uses `FOR UPDATE OF ss` in Postgres mode.
- Saga create binds native context values in Postgres mode and JSON text in sqlite mode.
- Saga row parsing preserves native Postgres JSONB dict/list values and decodes sqlite JSON text.
- Worker lease adapter tests prove native payload binding, lease_id conflict identity, generation preservation, duplicate event fallback, and transaction requirements.

## Verification

- P090 focused: 9 passed; selected saga/lease/Queue regression: 59 passed.
- P091 focused: 13 passed; selected saga/lease/Queue regression: 72 passed.
- P092 focused: 5 passed; selected worker lease/saga/Queue regression: 58 passed.
- Compileall and `git diff --check` succeeded for touched saga/lease test files during child verification.

## Known Gaps

- Live Postgres saga/lease runtime contention validation remains a later Queue staging validation problem.
- Session/outbox and transient error guard slices remain separate P074 children.

## Child Results

- R081
- R082
- R083
