# P285: Problem: Session compatibility and legacy residue audit

Status: done
Parent: P278
Root: P000
Source Ticket: T275 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P285
Body: problems/P000/children/P004/children/P278/children/P285/README.md
Ticket(s): T458

## Problem
Search for legacy session compatibility branches, old active-session APIs, direct saga creation bypasses, environment or global hidden inputs, and duplicate worker/session configuration that could keep old logic alive after the FSM migration.

## Success Criteria
- List searched residue patterns and matching files.
- Classify each match as active required path, safe legacy/documentation, risky compatibility branch, or removable residue.
- Create or recommend concrete cleanup follow-ups for risky/removable residue.

## Subproblems
- P465: Session legacy residue inventory
- P466: Session hidden input and duplicate config audit
- P467: Session legacy residue final verification

## Results
- R470

## Latest Check
C499

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P285/README.md
- Ticket T458: problems/P000/children/P004/children/P278/children/P285/tickets/T458.md
- Result R470: problems/P000/children/P004/children/P278/children/P285/results/R470.md
- Check C499: problems/P000/children/P004/children/P278/children/P285/checks/C499.md

## Follow-ups
- none
