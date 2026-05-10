# P003: Scope Transition Log Remediation

Status: done
Parent: P000
Root: P000
Package: problems/P000/children/P003
Body: problems/P000/children/P003/README.md
Ticket(s): T003

## Problem
`scope_state_log_path` writes a local best-effort NDJSON file outside LogicalFS. It is observability, not canonical authority, but it is still persistent state outside the clean model.

## Success Criteria
- Decide whether to move transition history to SQLite, LogicalFS, or an observability sink.
- Preserve replay/debug value without creating a second semantic authority.
- Define cleanup for local NDJSON path and tests around transition recording failure behavior.

## Subproblems
- none

## Results
- R002

## Latest Check
C002

## Bodies
- Problem: problems/P000/children/P003/README.md
- Ticket T003: problems/P000/children/P003/tickets/T003.md
- Result R002: problems/P000/children/P003/results/R002.md
- Check C002: problems/P000/children/P003/checks/C002.md

## Follow-ups
- none
