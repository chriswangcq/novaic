# P098: CI and Lint Helper Residue Scan

Status: done
Parent: P095
Root: P000
Source Ticket: T088 (split)
Source Check: none
Package: problems/P000/children/P001/children/P009/children/P017/children/P067/children/P093/children/P095/children/P098
Body: problems/P000/children/P001/children/P009/children/P017/children/P067/children/P093/children/P095/children/P098/README.md
Ticket(s): T090

## Problem
CI workflow files and lint/test helper scripts may contain stale compatibility, fallback, migration, or historical policy wording that no longer matches the final architecture.

## Success Criteria
- Scan `.github/`, CI config, and lint/test helper files for residue markers.
- Classify hits as active guard/policy, harmless fixture text, or stale residue.
- Remove safe stale residue.
- Run relevant lint/helper checks or explicit no-code-change verification.

## Subproblems
- none

## Results
- R083

## Latest Check
C097

## Bodies
- Problem: problems/P000/children/P001/children/P009/children/P017/children/P067/children/P093/children/P095/children/P098/README.md
- Ticket T090: problems/P000/children/P001/children/P009/children/P017/children/P067/children/P093/children/P095/children/P098/tickets/T090.md
- Result R083: problems/P000/children/P001/children/P009/children/P017/children/P067/children/P093/children/P095/children/P098/results/R083.md
- Check C097: problems/P000/children/P001/children/P009/children/P017/children/P067/children/P093/children/P095/children/P098/checks/C097.md

## Follow-ups
- none
