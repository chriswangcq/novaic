# P011: Phase 2B Scope Transition Write Cutover To SQLite

Status: done
Parent: P003
Root: P000
Package: problems/P000/children/P003/children/P011
Body: problems/P000/children/P003/children/P011/README.md
Ticket(s): T008

## Problem
Scope lifecycle transitions currently append durable rows through `scope_state_log.append_transition` into an NDJSON file. Change the canonical write path so non-noop transitions append to operational SQLite `scope_events` through explicit workspace/store dependencies.

## Success Criteria
- `scope_state.transition` or its immediate caller appends transition events to `OperationalSqliteStore.scope_events`.
- Transition events include root scope identity, scope id/path, from/to state, reason, actor, metadata, and created timestamp.
- Existing non-noop/idempotent behavior is preserved: noop transitions do not append.
- Tests prove child and root archive transitions write one SQLite event each.

## Subproblems
- P013: Require Operational Store For Scope Transition Writes

## Results
- R006

## Latest Check
C008

## Bodies
- Problem: problems/P000/children/P003/children/P011/README.md
- Ticket T008: problems/P000/children/P003/children/P011/tickets/T008.md
- Result R006: problems/P000/children/P003/children/P011/results/R006.md
- Check C006: problems/P000/children/P003/children/P011/checks/C006.md
- Check C008: problems/P000/children/P003/children/P011/checks/C008.md

## Follow-ups
- P013: Require Operational Store For Scope Transition Writes
