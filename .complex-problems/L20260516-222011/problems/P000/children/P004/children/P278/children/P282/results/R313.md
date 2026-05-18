# Session schema and state ownership audit result

## Summary

Completed the Queue Service session schema/state ownership audit through three closed child inventories. The current model is clean in the audited scope: `tq_session_state` is the authoritative materialized session state, `tq_session_events` is the append-only input/event log, `tq_session_outbox` is the durable side-effect ledger, and `tq_active_sessions` is not a live production table/read pointer.

## Done

- P286/R275/C290 mapped session schema tables and confirmed fresh DDL defines `tq_session_events`, `tq_session_state`, and `tq_session_outbox`; `tq_active_sessions` is absent from active DDL and production runtime references.
- P287/R307/C327 mapped session repository mutation surfaces and closed discovered residue/race issues: duplicated start-wake construction, pending-restart atomicity, eager attach publish ownership, and stale helper naming.
- P288/R312/C333 mapped rebuild/projection/read helpers and confirmed active reads derive from `tq_session_state` through `SessionLedgerRepository`; rebuild and pending projection are derived adapters, not second authorities.

## Verification

- P286 success check C290: schema and table-use inventory passed.
- P287 success check C327: mutation boundary inventory passed after follow-up fixes and guards.
- P288 success check C333: rebuild/projection/read inventory passed after stale PR-252 attach test update.
- Focused test evidence from child results includes session_state SSOT, active-session table removal, pending projection boundary, active state ledger boundary, rebuild projector boundary, projection quarantine, and attach outbox semantics.

## Known Gaps

- None for P282. Live production database migration state is outside this audit scope; this result covers source/schema/repository ownership in the current codebase.

## Artifacts

- `novaic-agent-runtime/queue_service/db/schema.py`
- `novaic-agent-runtime/queue_service/session_ledger.py`
- `novaic-agent-runtime/queue_service/session_repo.py`
- `novaic-agent-runtime/queue_service/session_rebuild.py`
- `novaic-agent-runtime/queue_service/session_projection.py`
- `novaic-agent-runtime/queue_service/session_outbox.py`
- Session ownership tests under `novaic-agent-runtime/tests/`
