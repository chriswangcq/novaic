# P014: Phase 2C1 Scope History API Reads From SQLite

Status: done
Parent: P012
Root: P000
Package: problems/P000/children/P003/children/P012/children/P014
Body: problems/P000/children/P003/children/P012/children/P014/README.md
Ticket(s): T011

## Problem
The `/v1/scope/history` endpoint still reads from the NDJSON transition log through `_registry.scope_state_log_path`. It must read from operational SQLite instead.

## Success Criteria
- `/v1/scope/history` calls `list_scope_transition_events(_registry.operational_store, ...)`.
- Response no longer includes `log_path`; it should indicate SQLite/operational backend if any backend field remains.
- Tests cover scope history rows coming from SQLite.

## Subproblems
- none

## Results
- R008

## Latest Check
C009

## Bodies
- Problem: problems/P000/children/P003/children/P012/children/P014/README.md
- Ticket T011: problems/P000/children/P003/children/P012/children/P014/tickets/T011.md
- Result R008: problems/P000/children/P003/children/P012/children/P014/results/R008.md
- Check C009: problems/P000/children/P003/children/P012/children/P014/checks/C009.md

## Follow-ups
- none
