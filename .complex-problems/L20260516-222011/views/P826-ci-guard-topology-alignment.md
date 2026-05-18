# P826: CI guard topology alignment

Status: done
Parent: P685
Root: P000
Source Ticket: T819 (split)
Source Check: none
Package: problems/P000/children/P007/children/P668/children/P673/children/P685/children/P826
Body: problems/P000/children/P007/children/P668/children/P673/children/P685/children/P826/README.md
Ticket(s): T822

## Problem
30+ CI lint scripts in scripts/ci/ check service boundaries, retired paths, and topology assumptions. These guards must reflect the current topology, not stale assumptions.

## Success Criteria
- CI guards that reference service boundaries or topology are identified.
- Guards checking for stale/retired paths are current.
- Running the relevant CI guards produces no false positives or stale failures.

## Subproblems
- none

## Results
- R817

## Latest Check
C866

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P673/children/P685/children/P826/README.md
- Ticket T822: problems/P000/children/P007/children/P668/children/P673/children/P685/children/P826/tickets/T822.md
- Result R817: problems/P000/children/P007/children/P668/children/P673/children/P685/children/P826/results/R817.md
- Check C866: problems/P000/children/P007/children/P668/children/P673/children/P685/children/P826/checks/C866.md

## Follow-ups
- none
