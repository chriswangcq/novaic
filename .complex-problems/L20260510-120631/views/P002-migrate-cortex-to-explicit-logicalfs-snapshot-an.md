# P002: Migrate Cortex to explicit LogicalFS snapshot and patch adapter

Status: done
Parent: P000
Root: P000
Package: problems/P000/children/P002
Body: problems/P000/children/P002/README.md
Ticket(s): T002

## Problem
Cortex should own workspace state but should not own filesystem materialization/diff implementation. It must export a snapshot and apply a returned patch through explicit adapter code.

## Success Criteria
- Cortex has a thin adapter that converts Workspace `/ro` and `/rw` data to LogicalFS snapshot DTOs.
- Cortex passes explicit env overlays, token, API URL, and RW layout values into LogicalFS instead of LogicalFS generating agent semantics.
- Cortex applies `WorkspacePatch` returned by LogicalFS.
- Old materialization/diff helpers are removed from Cortex or delegated to `novaic-logicalfs`.
- Cortex imports `logicalfs`, `sandbox_sdk`, and no `sandbox_core`.

## Subproblems
- none

## Results
- R001

## Latest Check
C001

## Bodies
- Problem: problems/P000/children/P002/README.md
- Ticket T002: problems/P000/children/P002/tickets/T002.md
- Result R001: problems/P000/children/P002/results/R001.md
- Check C001: problems/P000/children/P002/checks/C001.md

## Follow-ups
- none
