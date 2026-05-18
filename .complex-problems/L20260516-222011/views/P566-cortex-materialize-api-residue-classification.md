# P566: Cortex Materialize API Residue Classification

Status: done
Parent: P562
Root: P000
Source Ticket: T558 (split)
Source Check: none
Package: problems/P000/children/P005/children/P553/children/P562/children/P566
Body: problems/P000/children/P005/children/P553/children/P562/children/P566/README.md
Ticket(s): T559

## Problem
Classify Cortex occurrences of materialization APIs, especially `Workspace.materialize()`, direct `_files` access, and `/rw/scratch` writes, to determine whether they are intended compatibility surfaces or risky residue. This belongs under P562 because `Workspace.materialize()` was flagged by P552.

## Success Criteria
- Records exact Cortex scan commands and outputs for materialize/direct file terms.
- Reads relevant code slices with line references.
- Classifies each hit bucket as intended, risky, removable, or follow-up.
- Identifies any remediation candidate for P554.

## Subproblems
- none

## Results
- R555

## Latest Check
C589

## Bodies
- Problem: problems/P000/children/P005/children/P553/children/P562/children/P566/README.md
- Ticket T559: problems/P000/children/P005/children/P553/children/P562/children/P566/tickets/T559.md
- Result R555: problems/P000/children/P005/children/P553/children/P562/children/P566/results/R555.md
- Check C589: problems/P000/children/P005/children/P553/children/P562/children/P566/checks/C589.md

## Follow-ups
- none
