# P003: Clean stale workspace path residue safely

Status: done
Parent: P000
Root: P000
Source Ticket: T000 (split)
Source Check: none
Package: problems/P000/children/P003
Body: problems/P000/children/P003/README.md
Ticket(s): T003

## Problem
The working tree contains many stale problem-package paths and temporary files from earlier construction phases. Some may be useful history, some may be obsolete residue, and unrelated user changes must not be destroyed.

## Success Criteria
- Stale local residue is inventoried with path groups and disposition.
- Safe-to-delete residue is removed or archived only when it is not active product code and not needed for the current ledger.
- Current ledger files are preserved.
- Unrelated modified user files are left untouched unless explicitly identified as stale residue for this cleanup.
- Final `git status --short` is explained, including any remaining unrelated dirty files.

## Subproblems
- none

## Results
- R002

## Latest Check
C002

## Bodies
- Problem: problems/P000/children/P003/README.md
- Ticket T003: problems/P000/children/P003/tickets/T003.md
- Result R002: problems/P000/children/P003/results/R002.md
- Check C002: problems/P000/children/P003/checks/C002.md

## Follow-ups
- none
