# Check: Session schema and state ownership audit

## Summary

Success. The audit satisfies the original criteria with split child evidence rather than a shallow one-go pass. It maps the schema tables, repository mutation/read boundaries, rebuild/projection adapters, and duplicate active-session pointer risk. The only `tq_active_sessions` references found in the spot check are tests/residue guards, not production queue/task code.

## Evidence

- R313 aggregates three successful child problems: P286 schema table inventory, P287 repository mutation inventory, and P288 rebuild/projection/read inventory.
- R275/C290 maps session tables: `tq_session_events`, `tq_session_state`, and `tq_session_outbox`; `tq_active_sessions` is absent from fresh DDL and production runtime references in the audited code paths.
- R307/C327 maps repository mutation boundaries and closes discovered implementation residue/races instead of merely documenting them.
- R312/C333 maps active read, rebuild, and pending projection paths, proving active reads derive from `tq_session_state` through `SessionLedgerRepository`.
- Additional source spot-check during this check found session table DDL only for `tq_session_events`, `tq_session_state`, and `tq_session_outbox`; `tq_active_sessions` occurrences were in tests/guards, not production runtime paths.

## Criteria Map

- Map session-related tables and repository methods with file references: satisfied by R275, R307, and R312.
- State clearly whether `tq_session_state` is the authoritative state source: satisfied by R313 and child checks; active reads and rebuild writes route through `SessionLedgerRepository` / generic FSM store backed by `tq_session_state`.
- Identify duplicate active-session source that can drift or should be removed/demoted: satisfied. `tq_active_sessions` is classified as removed from active DDL/production code; pending projection is classified as derived observability, not an authority.

## Execution Map

- T276 split into P286, P287, and P288.
- P286 closed schema/table inventory with R275/C290.
- P287 closed repository mutation inventory with R307/C327 after recursive fixes.
- P288 closed rebuild/projection/read inventory with R312/C333 after a stale test was found and fixed.

## Stress Test

- False-clean schema risk: a removed table can still be read by production code. Checked by P286 and a fresh `rg` spot-check; no production runtime `tq_active_sessions` read path appeared.
- Dual-authority risk: pending projection could become a competing source. Checked by P288; it is derived from unconsumed input events and records observed projection events.
- Hidden mutation risk: repository could publish/modify state outside the ledger/outbox boundary. Checked by P287; discovered issues were fixed and guarded.

## Residual Risk

- Non-blocking: live deployed database contents and migration cleanup are outside P282. For source/schema/repository ownership in this codebase, the evidence is sufficient.

## Result IDs

- R313
- R275
- R307
- R312
