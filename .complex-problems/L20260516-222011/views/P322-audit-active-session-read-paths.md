# P322: Audit active session read paths

Status: done
Parent: P288
Root: P000
Source Ticket: T312 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P282/children/P288/children/P322
Body: problems/P000/children/P004/children/P278/children/P282/children/P288/children/P322/README.md
Ticket(s): T313

## Problem
Map active session read/list APIs and confirm they derive from session_state SSOT instead of legacy active-session pointers or caches.

## Success Criteria
- Read/list methods and callers are listed with file references.
- Source of truth for each active session read is classified.
- Any read path using stale pointer/cache state is flagged.

## Subproblems
- none

## Results
- R308

## Latest Check
C328

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P282/children/P288/children/P322/README.md
- Ticket T313: problems/P000/children/P004/children/P278/children/P282/children/P288/children/P322/tickets/T313.md
- Result R308: problems/P000/children/P004/children/P278/children/P282/children/P288/children/P322/results/R308.md
- Check C328: problems/P000/children/P004/children/P278/children/P282/children/P288/children/P322/checks/C328.md

## Follow-ups
- none
