# P631: Legacy RW Scratch Layout Cleanup

Status: done
Parent: P554
Root: P000
Source Ticket: T626 (split)
Source Check: none
Package: problems/P000/children/P005/children/P554/children/P631
Body: problems/P000/children/P005/children/P554/children/P631/README.md
Ticket(s): T630

## Problem
The old root-level `/rw/scratch` layout is classified as legacy residue around direct materialization. It should not remain as a default semantic path if the current model is subagent-aware LogicalFS-mounted RW layout.

## Success Criteria
- Scans all `/rw/scratch`, `scratch`, and related workspace layout usages.
- Classifies each hit as current intended scratch behavior, test fixture, or removable legacy layout.
- Removes or updates high-confidence legacy `/rw/scratch` assumptions and tests.
- Keeps any current scratch behavior explicitly justified and covered by tests.

## Subproblems
- P635: RW Scratch Usage Inventory
- P636: RW Scratch Layout Cleanup and Test Update
- P637: RW Scratch Final Guard

## Results
- R638

## Latest Check
C679

## Bodies
- Problem: problems/P000/children/P005/children/P554/children/P631/README.md
- Ticket T630: problems/P000/children/P005/children/P554/children/P631/tickets/T630.md
- Result R638: problems/P000/children/P005/children/P554/children/P631/results/R638.md
- Check C679: problems/P000/children/P005/children/P554/children/P631/checks/C679.md

## Follow-ups
- none
