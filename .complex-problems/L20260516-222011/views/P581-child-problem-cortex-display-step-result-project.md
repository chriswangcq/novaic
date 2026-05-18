# P581: Child Problem: Cortex display step-result projection contract

Status: done
Parent: P575
Root: P000
Source Ticket: T572 (split)
Source Check: none
Package: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P581
Body: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P581/README.md
Ticket(s): T583

## Problem
Audit Cortex/step-result formatting paths used by display to verify current-round display perception can expose media to runtime, while history/default projections expose bounded text and placeholders only.

## Success Criteria
- Records scan commands for step result formatting, projection mode handling, and display-specific projection code.
- Reads relevant Cortex/runtime bridge slices with line references.
- Classifies current perception and history projection behavior.
- Forwards any path that can replay display image bytes as ordinary text to P554.

## Subproblems
- none

## Results
- R578

## Latest Check
C616

## Bodies
- Problem: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P581/README.md
- Ticket T583: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P581/tickets/T583.md
- Result R578: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P581/results/R578.md
- Check C616: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P581/checks/C616.md

## Follow-ups
- none
