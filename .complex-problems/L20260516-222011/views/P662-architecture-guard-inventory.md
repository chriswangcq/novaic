# P662: Architecture guard inventory

Status: done
Parent: P661
Root: P000
Source Ticket: T660 (split)
Source Check: none
Package: problems/P000/children/P006/children/P661/children/P662
Body: problems/P000/children/P006/children/P661/children/P662/README.md
Ticket(s): T661

## Problem
Inventory existing CI/static guard scripts and module-level guard tests that protect old path removal, shell/display/tool-output contracts, lifecycle/session behavior, Blob/LogicalFS boundaries, generated artifacts, and deployment/runtime entrypoints.

## Success Criteria
- Lists relevant guard scripts/tests and the contract each protects.
- Identifies guard surfaces that are intentionally test-only versus CI script enforced.
- Saves inventory evidence in the ledger tmp directory.

## Subproblems
- none

## Results
- R658

## Latest Check
C700

## Bodies
- Problem: problems/P000/children/P006/children/P661/children/P662/README.md
- Ticket T661: problems/P000/children/P006/children/P661/children/P662/tickets/T661.md
- Result R658: problems/P000/children/P006/children/P661/children/P662/results/R658.md
- Check C700: problems/P000/children/P006/children/P661/children/P662/checks/C700.md

## Follow-ups
- none
