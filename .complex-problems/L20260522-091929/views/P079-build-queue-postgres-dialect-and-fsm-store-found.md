# P079: Build Queue Postgres Dialect And FSM Store Foundation

Status: done
Parent: P074
Root: P000
Source Ticket: T075 (split)
Source Check: none
Package: problems/P000/children/P024/children/P028/children/P074/children/P079
Body: problems/P000/children/P024/children/P028/children/P074/children/P079/README.md
Ticket(s): T076

## Problem
Queue's generic FSM persistence still lives in `queue_service/fsm/sqlite_store.py` and emits SQLite-oriented ordering, retry, and error semantics. Before task/saga/session repositories can be safely ported, Queue needs a Postgres-aware SQL dialect/store foundation that can express qmark-safe SQL, JSONB/timestamptz binding, deterministic ordering without `rowid`, and explicit transaction behavior under the Queue Postgres database boundary. This belongs under P074 because every repository port depends on a shared persistence foundation instead of duplicating dialect quirks.

## Success Criteria
- A Queue Postgres FSM store or dialect layer exists without relying on SQLite PRAGMAs, `rowid`, or SQLite busy string retries.
- Event/state/outbox append, upsert, list, mark-consumed, and claim-style operations have Postgres-safe SQL forms or clearly separated sqlite/postgres dialect branches.
- Ordering previously using `rowid` is replaced in the Postgres path with deterministic `(created_at, id)` or another explicit stable key.
- JSONB and timestamptz values are bound/decoded at the repository boundary without preserving long-term JSON text assumptions in the Postgres path.
- Focused tests cover generated SQL/behavior for the Postgres FSM store foundation and prove existing sqlite unit fixtures still pass.

## Subproblems
- none

## Results
- R073

## Latest Check
C078

## Bodies
- Problem: problems/P000/children/P024/children/P028/children/P074/children/P079/README.md
- Ticket T076: problems/P000/children/P024/children/P028/children/P074/children/P079/tickets/T076.md
- Result R073: problems/P000/children/P024/children/P028/children/P074/children/P079/results/R073.md
- Check C078: problems/P000/children/P024/children/P028/children/P074/children/P079/checks/C078.md

## Follow-ups
- none
