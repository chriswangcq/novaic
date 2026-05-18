# P290: Problem: Session table active usage classification

Status: done
Parent: P286
Root: P000
Source Ticket: T277 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P282/children/P286/children/P290
Body: problems/P000/children/P004/children/P278/children/P282/children/P286/children/P290/README.md
Ticket(s): T279

## Problem
For every session-related table found in DDL, scan active code references and classify the table's role in runtime behavior.

## Success Criteria
- List active read/write references per table with file references.
- Classify each table as authority, event log, durable outbox, projection/cache, or legacy residue.
- Identify any table name referenced in code but absent from DDL.

## Subproblems
- none

## Results
- R274

## Latest Check
C289

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P282/children/P286/children/P290/README.md
- Ticket T279: problems/P000/children/P004/children/P278/children/P282/children/P286/children/P290/tickets/T279.md
- Result R274: problems/P000/children/P004/children/P278/children/P282/children/P286/children/P290/results/R274.md
- Check C289: problems/P000/children/P004/children/P278/children/P282/children/P286/children/P290/checks/C289.md

## Follow-ups
- none
