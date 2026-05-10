# P030: Phase 3C1 SQLite Active Stack Read Adapter

Status: done
Parent: P019
Root: P000
Package: problems/P000/children/P004/children/P019/children/P030
Body: problems/P000/children/P004/children/P019/children/P030/README.md
Ticket(s): T026

## Problem
Runtime cutover needs one explicit adapter to read active-stack projection from operational SQLite and expose stable helpers for top frame, frame list, parent path, and response-compatible stack shape. Without this adapter, each API endpoint would duplicate SQLite row handling or keep using file-walk reads.

## Success Criteria
- Add a small read adapter/helper for SQLite active-stack projection.
- Adapter returns top-first frames and stack depth compatible with existing API responses.
- Adapter resolves current active scope path from the top frame `scope_path`, falling back to root only for empty stack.
- Adapter fails loudly for malformed non-empty frames missing `scope_path`.
- Focused tests cover empty and non-empty projections.

## Subproblems
- none

## Results
- R023

## Latest Check
C025

## Bodies
- Problem: problems/P000/children/P004/children/P019/children/P030/README.md
- Ticket T026: problems/P000/children/P004/children/P019/children/P030/tickets/T026.md
- Result R023: problems/P000/children/P004/children/P019/children/P030/results/R023.md
- Check C025: problems/P000/children/P004/children/P019/children/P030/checks/C025.md

## Follow-ups
- none
