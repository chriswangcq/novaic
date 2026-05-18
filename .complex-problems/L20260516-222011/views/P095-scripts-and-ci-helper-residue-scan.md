# P095: Scripts and CI Helper Residue Scan

Status: done
Parent: P093
Root: P000
Source Ticket: T086 (split)
Source Check: none
Package: problems/P000/children/P001/children/P009/children/P017/children/P067/children/P093/children/P095
Body: problems/P000/children/P001/children/P009/children/P017/children/P067/children/P093/children/P095/README.md
Ticket(s): T088

## Problem
Repository scripts, CI helpers, and shell lint/test scripts may contain stale compatibility, fallback, migration, or policy wording that no longer matches the final runtime/tool contract.

## Success Criteria
- Scan scripts and CI/test helper paths for residue markers.
- Classify hits as active policy/guard wording, harmless fixture text, or stale residue.
- Remove safe stale wording when found.
- Run relevant script/lint checks or record explicit no-code-change verification.

## Subproblems
- P097: Repository Scripts Residue Scan
- P098: CI and Lint Helper Residue Scan

## Results
- R084

## Latest Check
C098

## Bodies
- Problem: problems/P000/children/P001/children/P009/children/P017/children/P067/children/P093/children/P095/README.md
- Ticket T088: problems/P000/children/P001/children/P009/children/P017/children/P067/children/P093/children/P095/tickets/T088.md
- Result R084: problems/P000/children/P001/children/P009/children/P017/children/P067/children/P093/children/P095/results/R084.md
- Check C098: problems/P000/children/P001/children/P009/children/P017/children/P067/children/P093/children/P095/checks/C098.md

## Follow-ups
- none
