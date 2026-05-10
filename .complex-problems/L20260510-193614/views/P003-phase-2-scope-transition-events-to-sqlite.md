# P003: Phase 2 Scope Transition Events To SQLite

Status: done
Parent: P000
Root: P000
Package: problems/P000/children/P003
Body: problems/P000/children/P003/README.md
Ticket(s): T006

## Problem
Scope transition history is currently written to local NDJSON. Move this to the SQLite operational store.

## Success Criteria
- `scope_state.transition` records lifecycle events through the SQLite store.
- Runtime no longer requires local `scope_state_log_path` as authority.
- Tests cover transition recording, idempotent self-loop behavior, and failure semantics.

## Subproblems
- P010: Phase 2A Scope Transition Callsite And Semantics Audit
- P011: Phase 2B Scope Transition Write Cutover To SQLite
- P012: Phase 2C Scope History Read Cutover And NDJSON Cleanup

## Results
- R012

## Latest Check
C013

## Bodies
- Problem: problems/P000/children/P003/README.md
- Ticket T006: problems/P000/children/P003/tickets/T006.md
- Result R012: problems/P000/children/P003/results/R012.md
- Check C013: problems/P000/children/P003/checks/C013.md

## Follow-ups
- none
