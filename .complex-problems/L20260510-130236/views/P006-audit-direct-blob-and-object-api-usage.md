# P006: Audit direct Blob and object API usage

Status: done
Parent: P004
Root: P000
Package: problems/P000/children/P004/children/P006
Body: problems/P000/children/P004/children/P006/README.md
Ticket(s): T005

## Problem
Find every direct Blob/object API usage relevant to Cortex, LogicalFS, sandboxd,
runtime, app/display/artifact bytes, and docs. Classify each as allowed or a
blocking live `RO` / `RW` bypass.

## Success Criteria
- Source pointers list all relevant direct Blob/object uses in Cortex and nearby
- services.
- Each usage is classified as allowed cheap-byte use, allowed persistence
- adapter/internal use, test-only use, stale doc/comment, or blocking bypass.
- The result identifies exact cleanup or guardrail follow-up work.

## Subproblems
- none

## Results
- R003

## Latest Check
C003

## Bodies
- Problem: problems/P000/children/P004/children/P006/README.md
- Ticket T005: problems/P000/children/P004/children/P006/tickets/T005.md
- Result R003: problems/P000/children/P004/children/P006/results/R003.md
- Check C003: problems/P000/children/P004/children/P006/checks/C003.md

## Follow-ups
- none
