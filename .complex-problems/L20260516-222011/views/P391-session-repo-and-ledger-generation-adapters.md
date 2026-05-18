# P391: Session repo and ledger generation adapters

Status: done
Parent: P389
Root: P000
Source Ticket: T380 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/children/P389/children/P391
Body: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/children/P389/children/P391/README.md
Ticket(s): T382

## Problem
`session_repo.py` and `session_ledger.py` still contain raw generation defaults in state reconstruction and ledger generation helpers. These need to be either fixed as live authority paths or classified as safe persistence adapters with tests.

## Success Criteria
- Runtime state reconstruction rejects malformed active/session state generation where it affects authority decisions.
- Ledger active generation helpers are either replaced with explicit validators or documented/test-covered as internal DB integer adapters.
- Focused session repo/ledger tests pass.
- Guard matrix classifies all remaining repo/ledger generation hits.

## Subproblems
- P394: Session repo state reconstruction validation
- P395: Session ledger generation helper classification

## Results
- R376

## Latest Check
C399

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/children/P389/children/P391/README.md
- Ticket T382: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/children/P389/children/P391/tickets/T382.md
- Result R376: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/children/P389/children/P391/results/R376.md
- Check C399: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/children/P389/children/P391/checks/C399.md

## Follow-ups
- none
