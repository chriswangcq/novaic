# P153: context.jsonl caller classification

Status: done
Parent: P143
Root: P000
Source Ticket: T137 (split)
Source Check: none
Package: problems/P000/children/P003/children/P126/children/P134/children/P143/children/P153
Body: problems/P000/children/P003/children/P126/children/P134/children/P143/children/P153/README.md
Ticket(s): T139

## Problem
All active callers of `context.jsonl` helpers must be classified as debug projection, compatibility path, active source, or stale. Unclassified callers are a source-of-truth ambiguity.

This belongs under `P143` because the project needs a concrete caller map before deciding whether code should stay or be removed.

## Success Criteria
- Repository-wide helper call sites are listed with source pointers.
- Each non-test caller is classified precisely.
- Any stale or unsafe caller is fixed, removed, or split into a follow-up.

## Subproblems
- none

## Results
- R134

## Latest Check
C148

## Bodies
- Problem: problems/P000/children/P003/children/P126/children/P134/children/P143/children/P153/README.md
- Ticket T139: problems/P000/children/P003/children/P126/children/P134/children/P143/children/P153/tickets/T139.md
- Result R134: problems/P000/children/P003/children/P126/children/P134/children/P143/children/P153/results/R134.md
- Check C148: problems/P000/children/P003/children/P126/children/P134/children/P143/children/P153/checks/C148.md

## Follow-ups
- none
