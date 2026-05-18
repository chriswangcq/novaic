# P114: Cortex Stable Workspace Path Contract Audit

Status: done
Parent: P107
Root: P000
Source Ticket: T106 (split)
Source Check: none
Package: problems/P000/children/P002/children/P103/children/P107/children/P114
Body: problems/P000/children/P002/children/P103/children/P107/children/P114/README.md
Ticket(s): T108

## Problem
Agents should use `/cortex/ro`, `/cortex/rw`, `$RO`, and `$RW`, not copied `novaic-cortex-sandbox-*` backing paths. Stable path guidance and runtime guards must be visible and tested.

## Success Criteria
- Inspect shell schema/help/docs for stable path guidance.
- Verify runtime rejects or discourages stale backing paths.
- Run focused runtime/Cortex path abuse tests.
- Fix bounded guidance or guard gaps found.

## Subproblems
- P115: Stable Workspace Path Guidance in Shell Schema and Help
- P116: Runtime Stale Cortex Backing Path Rejection Guard
- P117: Stable Workspace Path Docs and Example Residue Sweep
- P118: Stable Workspace Path Regression Sweep

## Results
- R111

## Latest Check
C125

## Bodies
- Problem: problems/P000/children/P002/children/P103/children/P107/children/P114/README.md
- Ticket T108: problems/P000/children/P002/children/P103/children/P107/children/P114/tickets/T108.md
- Result R111: problems/P000/children/P002/children/P103/children/P107/children/P114/results/R111.md
- Check C125: problems/P000/children/P002/children/P103/children/P107/children/P114/checks/C125.md

## Follow-ups
- none
