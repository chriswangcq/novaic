# P020: Audit Active RO/RW Authority And Construction Paths

Status: done
Parent: P019
Root: P000
Package: problems/P000/children/P019/children/P020
Body: problems/P000/children/P019/children/P020/README.md
Ticket(s): T020

## Problem
Before moving the authority boundary, identify every active code path that constructs or uses live Cortex `RO` / `RW` file access, including Workspace, runtime, API, registry, shell/sandbox integration, tests, and docs that might encode the old architecture. This belongs under T019 because a boundary migration without a precise path audit can leave new code unconnected while production still runs the old implementation.

## Success Criteria
- Active Workspace/runtime/API/registry construction paths are mapped with file and symbol pointers.
- All direct uses of `CortexLogicalFileAuthority`, `CortexStore`, `BlobCortexStore`, `ws._store`, and `/v1/objects` in live paths are classified as active, test-only, docs, or removable residue.
- The audit identifies the smallest safe implementation slices and any tests that must change.
- The result explicitly lists no-go hidden dependencies that later tickets must remove or guard.

## Subproblems
- none

## Results
- R019

## Latest Check
C019

## Bodies
- Problem: problems/P000/children/P019/children/P020/README.md
- Ticket T020: problems/P000/children/P019/children/P020/tickets/T020.md
- Result R019: problems/P000/children/P019/children/P020/results/R019.md
- Check C019: problems/P000/children/P019/children/P020/checks/C019.md

## Follow-ups
- none
