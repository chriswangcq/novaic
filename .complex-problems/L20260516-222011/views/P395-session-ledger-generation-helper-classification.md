# P395: Session ledger generation helper classification

Status: done
Parent: P391
Root: P000
Source Ticket: T382 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/children/P389/children/P391/children/P395
Body: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/children/P389/children/P391/children/P395/README.md
Ticket(s): T384

## Problem
`session_ledger.py` uses raw `int(current.get("generation") or 0)` in active generation helpers. These are DB authority helpers and must either validate stored generation explicitly or be classified as safe integer DB adapters.

## Success Criteria
- Session ledger active generation read/increment helpers validate DB generation without accepting bool/malformed values.
- Existing session ledger behavior for no row/no active state remains correct.
- Focused tests cover malformed stored generation if directly injectable, or source classification explains why SQLite schema prevents it.
- Targeted guard no longer reports unclassified session ledger generation defaults.

## Subproblems
- none

## Results
- R375

## Latest Check
C398

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/children/P389/children/P391/children/P395/README.md
- Ticket T384: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/children/P389/children/P391/children/P395/tickets/T384.md
- Result R375: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/children/P389/children/P391/children/P395/results/R375.md
- Check C398: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/children/P389/children/P391/children/P395/checks/C398.md

## Follow-ups
- none
