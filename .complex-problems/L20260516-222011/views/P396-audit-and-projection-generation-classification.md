# P396: Audit and projection generation classification

Status: done
Parent: P392
Root: P000
Source Ticket: T385 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/children/P389/children/P392/children/P396
Body: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/children/P389/children/P392/children/P396/README.md
Ticket(s): T386

## Problem
`session_audit.py`, `queue_audit.py`, and related projection helpers still contain raw generation defaults. They are likely read-only diagnostics/projections, but must be explicitly classified or patched.

## Success Criteria
- Audit/projection generation hits are enumerated with file evidence.
- Hits are either patched to explicit validators or classified safe as diagnostic/projection formatting.
- Any changed audit/projection tests pass.

## Subproblems
- none

## Results
- R377

## Latest Check
C400

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/children/P389/children/P392/children/P396/README.md
- Ticket T386: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/children/P389/children/P392/children/P396/tickets/T386.md
- Result R377: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/children/P389/children/P392/children/P396/results/R377.md
- Check C400: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/children/P389/children/P392/children/P396/checks/C400.md

## Follow-ups
- none
