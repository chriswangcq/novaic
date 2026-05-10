# P025: Add Cortex Workspace LogicalFS Factory And Test Authority Helper

Status: done
Parent: P023
Root: P000
Package: problems/P000/children/P019/children/P023/children/P025
Body: problems/P000/children/P019/children/P023/children/P025/README.md
Ticket(s): T024

## Problem
Tests and constructors currently create Cortex workspaces from `MemoryStore` or other direct store-shaped objects. Before cutting the active constructor, Cortex needs an explicit helper/factory that builds `StoreBackedLogicalFileAuthority` with explicit owner layout, so tests and runtime wiring have a clear replacement path. This belongs under P023 because constructor migration needs a safe explicit authority creation seam.

## Success Criteria
- Cortex has a small helper/factory for creating a LogicalFS-backed Workspace authority from an object store and agent id.
- The helper passes explicit `LogicalFileAuthorityLayout(owner_prefix=...)`.
- Tests can use the helper without importing or touching `CortexLogicalFileAuthority`.
- The helper does not become a hidden compatibility constructor that accepts arbitrary old arguments in `Workspace`.

## Subproblems
- none

## Results
- R022

## Latest Check
C022

## Bodies
- Problem: problems/P000/children/P019/children/P023/children/P025/README.md
- Ticket T024: problems/P000/children/P019/children/P023/children/P025/tickets/T024.md
- Result R022: problems/P000/children/P019/children/P023/children/P025/results/R022.md
- Check C022: problems/P000/children/P019/children/P023/children/P025/checks/C022.md

## Follow-ups
- none
