# P782: Active Docs Boundary Wording Remediation

Status: done
Parent: P750
Root: P000
Source Ticket: T774 (split)
Source Check: none
Package: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P782
Body: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P782/README.md
Ticket(s): T775

## Problem
Patch active architecture/docs wording that overstates ownership or mixes semantic authority with file-operation substrate authority.

## Success Criteria
- `docs/architecture/logicalfs-realtime-file-authority.md` distinguishes Cortex semantic ownership from LogicalFS file-operation/view authority.
- `docs/architecture/cortex.md` and `docs/cortex-architecture.md` describe Cortex as orchestrating shell/workspace semantics while delegating process execution to Sandboxd and file operations to LogicalFS.
- `docs/architecture/data-ownership.md` clearly separates Cortex scope/context/workspace semantics, LogicalFS live RO/RW operations/view contract, and Blob byte/object ownership.
- Changes are wording-only and do not introduce new architecture claims not supported by code.

## Subproblems
- none

## Results
- R767

## Latest Check
C813

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P782/README.md
- Ticket T775: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P782/tickets/T775.md
- Result R767: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P782/results/R767.md
- Check C813: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P782/checks/C813.md

## Follow-ups
- none
