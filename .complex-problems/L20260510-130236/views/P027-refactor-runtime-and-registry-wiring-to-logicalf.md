# P027: Refactor Runtime And Registry Wiring To LogicalFS Authority

Status: done
Parent: P023
Root: P000
Package: problems/P000/children/P019/children/P023/children/P027
Body: problems/P000/children/P019/children/P023/children/P027/README.md
Ticket(s): T026

## Problem
Runtime and registry construction still preserve old direct-store semantics: registry caches a lower object adapter and passes it directly to Workspace, and `Cortex.__init__` accepts `store, agent_id`. This belongs under P023 because active agent runtime must be wired through the LogicalFS authority boundary.

## Success Criteria
- `WorkspaceRegistry` constructs a LogicalFS authority and passes it to `Workspace`.
- `Cortex.__init__` no longer exposes the old `store, agent_id` live constructor path.
- API `_build_cortex(ws)` remains workspace-based and does not regress to store construction.
- Runtime tests use explicit workspace/factory helpers instead of direct store arguments.
- Source scans show no direct store construction in runtime/registry active paths.

## Subproblems
- none

## Results
- R024

## Latest Check
C024

## Bodies
- Problem: problems/P000/children/P019/children/P023/children/P027/README.md
- Ticket T026: problems/P000/children/P019/children/P023/children/P027/tickets/T026.md
- Result R024: problems/P000/children/P019/children/P023/children/P027/results/R024.md
- Check C024: problems/P000/children/P019/children/P023/children/P027/checks/C024.md

## Follow-ups
- none
