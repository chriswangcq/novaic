# P003: Cut Over Active Shell Path And Remove Old Branches

Status: done
Parent: P000
Root: P000
Package: problems/P000/children/P003
Body: problems/P000/children/P003/README.md
Ticket(s): T003

## Problem
Route the active shell execution path through the new boundary and physically remove or quarantine the old command-gated temp-projection logic. This closes the common failure mode where new code exists but old logic still runs.

## Success Criteria
- `Sandbox.exec` routes through ShellExecutionOrchestrator.
- Command-string RO gating is removed from active code.
- Old `_materialize_workspace` and `_persist_rw_changes` authority is removed from `Sandbox`.
- Tests no longer encode lazy-RO behavior as desired.
- `rg` audit proves old command-gating symbols are absent or unreachable.

## Subproblems
- none

## Results
- R002

## Latest Check
C002

## Bodies
- Problem: problems/P000/children/P003/README.md
- Ticket T003: problems/P000/children/P003/tickets/T003.md
- Result R002: problems/P000/children/P003/results/R002.md
- Check C002: problems/P000/children/P003/checks/C002.md

## Follow-ups
- none
