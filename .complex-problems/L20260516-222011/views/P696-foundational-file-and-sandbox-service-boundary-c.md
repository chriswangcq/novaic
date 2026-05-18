# P696: Foundational file and sandbox service boundary classification

Status: done
Parent: P684
Root: P000
Source Ticket: T689 (split)
Source Check: none
Package: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P696
Body: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P696/README.md
Ticket(s): T691

## Problem
Classify Blob, LogicalFS, and Sandbox/Sandboxd as foundational infrastructure services. Verify their entrypoints, roles, and dependency boundaries, especially that Blob remains a cheap file server, LogicalFS owns realtime RO/RW logical file behavior, and Sandbox/Sandboxd owns execution/mount behavior without hidden Cortex ownership.

## Success Criteria
- Blob, LogicalFS, and Sandbox/Sandboxd each have role, entrypoint, and dependency-boundary evidence.
- Any Cortex-to-foundational-service calls are classified as service usage rather than ownership.
- Any stale code/docs implying Cortex owns foundational file/sandbox internals are patched or recorded.
- Touched files receive focused syntax/static checks.

## Subproblems
- P699: Blob service boundary map
- P700: LogicalFS boundary map
- P701: Sandbox and Sandboxd boundary map
- P702: Foundational boundary residue cleanup and verification

## Results
- R692

## Latest Check
C735

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P696/README.md
- Ticket T691: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P696/tickets/T691.md
- Result R692: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P696/results/R692.md
- Check C735: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P696/checks/C735.md

## Follow-ups
- none
