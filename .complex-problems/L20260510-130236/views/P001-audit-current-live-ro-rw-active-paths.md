# P001: Audit current live RO/RW active paths

Status: done
Parent: P000
Root: P000
Package: problems/P000/children/P001
Body: problems/P000/children/P001/README.md
Ticket(s): T001

## Problem
Before implementing more code, audit the current active paths for Cortex shell
execution, Workspace persistence, LogicalFS, sandboxd, and Blob object use. The
goal is to distinguish already-cut-over paths from old paths that still execute
in production.

## Success Criteria
- Source pointers identify the active shell execution path from tool call to
- LogicalFS and sandboxd.
- Source pointers identify all direct Cortex/Runtime/Sandbox Blob object use
- that could affect live `RO` / `RW`.
- The audit classifies each path as target, transitional, legacy inactive, or
- blocking gap.
- The result becomes the implementation checklist for later child problems.

## Subproblems
- none

## Results
- R000

## Latest Check
C000

## Bodies
- Problem: problems/P000/children/P001/README.md
- Ticket T001: problems/P000/children/P001/tickets/T001.md
- Result R000: problems/P000/children/P001/results/R000.md
- Check C000: problems/P000/children/P001/checks/C000.md

## Follow-ups
- none
