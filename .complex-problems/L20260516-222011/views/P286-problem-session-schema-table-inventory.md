# P286: Problem: Session schema table inventory

Status: done
Parent: P282
Root: P000
Source Ticket: T276 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P282/children/P286
Body: problems/P000/children/P004/children/P278/children/P282/children/P286/README.md
Ticket(s): T277

## Problem
Inspect Queue Service schema definitions and migrations for session-related tables and indexes so the state ownership audit starts from actual persisted structures.

## Success Criteria
- List every session-related table/index found with file references.
- Explain each table's intended role from schema and nearby code names.
- Identify whether `tq_active_sessions` exists as a table, view, or absent artifact.

## Subproblems
- P289: Problem: Session DDL definition scan
- P290: Problem: Session table active usage classification

## Results
- R275

## Latest Check
C290

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P282/children/P286/README.md
- Ticket T277: problems/P000/children/P004/children/P278/children/P282/children/P286/tickets/T277.md
- Result R275: problems/P000/children/P004/children/P278/children/P282/children/P286/results/R275.md
- Check C290: problems/P000/children/P004/children/P278/children/P282/children/P286/checks/C290.md

## Follow-ups
- none
