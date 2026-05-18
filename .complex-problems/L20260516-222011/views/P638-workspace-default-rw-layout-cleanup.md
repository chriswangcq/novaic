# P638: Workspace Default RW Layout Cleanup

Status: done
Parent: P636
Root: P000
Source Ticket: T632 (split)
Source Check: none
Package: problems/P000/children/P005/children/P554/children/P631/children/P636/children/P638
Body: problems/P000/children/P005/children/P554/children/P631/children/P636/children/P638/README.md
Ticket(s): T633

## Problem
Workspace initialization still creates `/rw/scratch` as a default directory. That is the production layout residue to remove before tests can stop treating it as canonical.

## Success Criteria
- Removes `/rw/scratch` from `Workspace.initialize()` default layout.
- Updates direct initialization assertions to match the current default layout.
- Runs focused Workspace initialization tests.

## Subproblems
- none

## Results
- R628

## Latest Check
C669

## Bodies
- Problem: problems/P000/children/P005/children/P554/children/P631/children/P636/children/P638/README.md
- Ticket T633: problems/P000/children/P005/children/P554/children/P631/children/P636/children/P638/tickets/T633.md
- Result R628: problems/P000/children/P005/children/P554/children/P631/children/P636/children/P638/results/R628.md
- Check C669: problems/P000/children/P005/children/P554/children/P631/children/P636/children/P638/checks/C669.md

## Follow-ups
- none
