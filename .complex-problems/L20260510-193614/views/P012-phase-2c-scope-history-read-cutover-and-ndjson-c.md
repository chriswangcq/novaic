# P012: Phase 2C Scope History Read Cutover And NDJSON Cleanup

Status: done
Parent: P003
Root: P000
Package: problems/P000/children/P003/children/P012
Body: problems/P000/children/P003/children/P012/README.md
Ticket(s): T010

## Problem
The `/v1/scope/history` read path and scope transition tests still assume the NDJSON transition log is the machine-readable authority. Move history reads to SQLite and remove or explicitly demote old NDJSON wiring.

## Success Criteria
- `/v1/scope/history` reads transition history from operational SQLite.
- `scope_state_log_path` is removed from required Cortex startup/registry/workspace construction if no longer needed.
- Tests no longer require a transition NDJSON path for authoritative lifecycle history.
- Static searches show any remaining `scope_state_log`/NDJSON code is deleted or clearly projection/debug-only.

## Subproblems
- P014: Phase 2C1 Scope History API Reads From SQLite
- P015: Phase 2C2 Remove NDJSON Transition Log Surface
- P016: Phase 2C3 Transition Cleanup Verification

## Results
- R011

## Latest Check
C012

## Bodies
- Problem: problems/P000/children/P003/children/P012/README.md
- Ticket T010: problems/P000/children/P003/children/P012/tickets/T010.md
- Result R011: problems/P000/children/P003/children/P012/results/R011.md
- Check C012: problems/P000/children/P003/children/P012/checks/C012.md

## Follow-ups
- none
