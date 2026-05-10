# P049: Migrate archive and summary lifecycle tests

Status: done
Parent: P047
Root: P000
Package: problems/P000/children/P004/children/P028/children/P043/children/P047/children/P049
Body: problems/P000/children/P004/children/P028/children/P043/children/P047/children/P049/README.md
Ticket(s): T044

## Problem
Archive/summary tests currently use `cortex.scope_end(...)` to close scopes. That removed runtime helper must be replaced with event-wired API lifecycle handlers without changing the archive invariant being tested.

## Success Criteria
- `tests/test_archive_invariants.py` no longer calls `cortex.scope_end(...)`.
- `tests/test_pr74_scope_summary_contract.py` no longer calls `cortex.scope_end(...)`.
- Tests that validate structural scope ending use `novaic_cortex.api.scope_end` with `ScopeEndRequest`.
- Focused archive/summary tests pass.

## Subproblems
- none

## Results
- R039

## Latest Check
C042

## Bodies
- Problem: problems/P000/children/P004/children/P028/children/P043/children/P047/children/P049/README.md
- Ticket T044: problems/P000/children/P004/children/P028/children/P043/children/P047/children/P049/tickets/T044.md
- Result R039: problems/P000/children/P004/children/P028/children/P043/children/P047/children/P049/results/R039.md
- Check C042: problems/P000/children/P004/children/P028/children/P043/children/P047/children/P049/checks/C042.md

## Follow-ups
- none
