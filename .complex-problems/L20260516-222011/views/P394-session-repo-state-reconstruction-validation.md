# P394: Session repo state reconstruction validation

Status: done
Parent: P391
Root: P000
Source Ticket: T382 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/children/P389/children/P391/children/P394
Body: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/children/P389/children/P391/children/P394/README.md
Ticket(s): T383

## Problem
`session_repo.py` uses raw defaults when converting active/session state dictionaries into `SessionRuntimeState`. These conversions feed dispatch/finalize decisions and should explicitly distinguish no-active generation `0` from malformed active-state generation.

## Success Criteria
- Runtime state reconstruction validates active/ending/recovering/suspected-dead generation explicitly.
- No-active state still permits generation `0`.
- Focused session repo/FSM tests cover malformed active generation rejection.
- Targeted guard no longer reports unclassified repo reconstruction generation defaults.

## Subproblems
- none

## Results
- R374

## Latest Check
C397

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/children/P389/children/P391/children/P394/README.md
- Ticket T383: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/children/P389/children/P391/children/P394/tickets/T383.md
- Result R374: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/children/P389/children/P391/children/P394/results/R374.md
- Check C397: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/children/P389/children/P391/children/P394/checks/C397.md

## Follow-ups
- none
