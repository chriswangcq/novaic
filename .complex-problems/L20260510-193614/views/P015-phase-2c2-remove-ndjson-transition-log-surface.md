# P015: Phase 2C2 Remove NDJSON Transition Log Surface

Status: done
Parent: P012
Root: P000
Package: problems/P000/children/P003/children/P012/children/P015
Body: problems/P000/children/P003/children/P012/children/P015/README.md
Ticket(s): T012

## Problem
After history reads move to SQLite, NDJSON transition helpers and startup/config fields should be physically removed. Leaving them creates misleading dual-source residue.

## Success Criteria
- Remove `scope_state_log_path` from `Workspace`, `WorkspaceRegistry`, `build_workspace_registry`, `main_cortex.py`, `scripts/start.sh`, docs, and tests.
- Remove `transition_log_path` from `scope_state.transition` and `mark_archived`.
- Delete `novaic_cortex/scope_state_log.py` and its direct NDJSON tests.
- Static search for `scope_state_log_path`, `transition_log_path`, and `scope_state_log` has no live authoritative code matches.

## Subproblems
- none

## Results
- R009

## Latest Check
C010

## Bodies
- Problem: problems/P000/children/P003/children/P012/children/P015/README.md
- Ticket T012: problems/P000/children/P003/children/P012/children/P015/tickets/T012.md
- Result R009: problems/P000/children/P003/children/P012/children/P015/results/R009.md
- Check C010: problems/P000/children/P003/children/P012/children/P015/checks/C010.md

## Follow-ups
- none
