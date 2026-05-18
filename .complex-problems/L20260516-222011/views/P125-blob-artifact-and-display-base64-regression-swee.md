# P125: Blob Artifact and Display Base64 Regression Sweep

Status: done
Parent: P104
Root: P000
Source Ticket: T116 (split)
Source Check: none
Package: problems/P000/children/P002/children/P104/children/P125
Body: problems/P000/children/P002/children/P104/children/P125/README.md
Ticket(s): T120

## Problem
After artifact CLI and display projection checks, run a final regression sweep for base64/data URL leakage in shell/display history contracts.

## Success Criteria
- Run focused runtime/Cortex tests for tool-output manifests, display history, and no historical tool image injection.
- Search active code/tests for raw media/base64 transport paths and classify allowed protocol-local uses.
- Add or adjust the smallest regression guard if an uncovered leak path remains.

## Subproblems
- none

## Results
- R117

## Latest Check
C131

## Bodies
- Problem: problems/P000/children/P002/children/P104/children/P125/README.md
- Ticket T120: problems/P000/children/P002/children/P104/children/P125/tickets/T120.md
- Result R117: problems/P000/children/P002/children/P104/children/P125/results/R117.md
- Check C131: problems/P000/children/P002/children/P104/children/P125/checks/C131.md

## Follow-ups
- none
