# P007: CI Bytecode And Generated Artifact Hygiene

Status: done
Parent: P000
Root: P000
Package: problems/P000/children/P007
Body: problems/P000/children/P007/README.md
Ticket(s): T007

## Problem
Python lints/tests can generate `__pycache__`, causing generated-artifacts lint to fail when commands are chained. Standardize guard invocation or cleanup so generated artifact checks are stable.

## Success Criteria
- CI guard scripts or documented command wrappers use `PYTHONDONTWRITEBYTECODE=1` where appropriate.
- Generated-artifact lint passes after the normal guard sequence.
- Any generated cache artifacts from local verification are cleaned.

## Subproblems
- none

## Results
- R006

## Latest Check
C006

## Bodies
- Problem: problems/P000/children/P007/README.md
- Ticket T007: problems/P000/children/P007/tickets/T007.md
- Result R006: problems/P000/children/P007/results/R006.md
- Check C006: problems/P000/children/P007/checks/C006.md

## Follow-ups
- none
