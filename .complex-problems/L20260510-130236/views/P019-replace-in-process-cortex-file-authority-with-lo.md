# P019: Replace In-Process Cortex File Authority With LogicalFS Boundary

Status: done
Parent: P000
Root: P000
Package: problems/P000/children/P019
Body: problems/P000/children/P019/README.md
Ticket(s): T019

## Problem
The current implementation routes active Cortex `RO` / `RW` operations through `CortexLogicalFileAuthority`, which is an improvement, but the authority still lives inside `novaic-cortex` and persists through `CortexStore`. The final target requires LogicalFS to be the live file authority boundary, with Cortex passing explicit semantic owner/layout inputs and no direct Cortex-owned persistence adapter for live file operations.

## Success Criteria
- Cortex Workspace live file operations call a LogicalFS boundary/port instead of directly owning the store adapter.
- The transitional `CortexLogicalFileAuthority -> CortexStore` path is removed or downgraded to a test-only/local implementation behind the LogicalFS boundary.
- `BlobCortexStore` is no longer reachable from live Workspace/registry construction except as a LogicalFS-internal persistence adapter.
- Tests prove Workspace/API/runtime/sandbox active paths still work through the LogicalFS boundary.
- Residue scans fail direct live Workspace use of `CortexStore`, `BlobCortexStore`, or `/v1/objects` outside the LogicalFS boundary.

## Subproblems
- P020: Audit Active RO/RW Authority And Construction Paths
- P021: Add Generic LogicalFS Live File Authority
- P022: Move Blob Object Persistence Below LogicalFS
- P023: Cut Cortex Workspace Runtime To LogicalFS Authority
- P024: Delete Old Authority Paths And Strengthen Guardrails

## Results
- R035

## Latest Check
C035

## Bodies
- Problem: problems/P000/children/P019/README.md
- Ticket T019: problems/P000/children/P019/tickets/T019.md
- Result R035: problems/P000/children/P019/results/R035.md
- Check C035: problems/P000/children/P019/checks/C035.md

## Follow-ups
- none
