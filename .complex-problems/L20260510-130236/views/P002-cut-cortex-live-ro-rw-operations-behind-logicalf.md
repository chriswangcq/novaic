# P002: Cut Cortex live RO/RW operations behind LogicalFS

Status: done
Parent: P000
Root: P000
Package: problems/P000/children/P002
Body: problems/P000/children/P002/README.md
Ticket(s): T002

## Problem
Cortex owns scope/workspace semantics, but live file operations for shell
`RO` / `RW` must be owned by LogicalFS. Any direct live Workspace persistence
or shell file operation that bypasses LogicalFS must be migrated or explicitly
removed if obsolete.

## Success Criteria
- Cortex shell execution uses LogicalFS for materialization, stable paths, and
- patch observation/application.
- Workspace file operations that participate in live `RO` / `RW` are routed
- through LogicalFS or clearly isolated as non-live migration/storage internals.
- Tests prove shell output sanitization and file update persistence still work.
- No local fallback path silently executes shell without sandboxd/LogicalFS.

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
