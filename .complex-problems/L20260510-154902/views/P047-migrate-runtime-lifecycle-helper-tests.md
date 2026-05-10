# P047: Migrate runtime lifecycle helper tests

Status: done
Parent: P043
Root: P000
Package: problems/P000/children/P004/children/P028/children/P043/children/P047
Body: problems/P000/children/P004/children/P028/children/P043/children/P047/README.md
Ticket(s): T043

## Problem
Multiple older tests call `cortex.scope_create(...)` or `cortex.scope_end(...)` for convenience. Once runtime lifecycle helpers are removed, those tests must be rewritten to the event-wired API path or converted to guard/obsolete behavior tests without preserving the bypass.

## Success Criteria
- No test uses `cortex.scope_create(...)` or `cortex.scope_end(...)`.
- Tests that still need lifecycle setup use `novaic_cortex.api.scope_create` / `scope_end` request handlers or lower-level projection helpers only when explicitly testing projections.
- Obsolete hook/metric expectations tied only to runtime lifecycle helpers are removed or replaced with relevant tool-facing/API-facing assertions.
- Focused migrated test files pass.

## Subproblems
- P049: Migrate archive and summary lifecycle tests
- P050: Migrate hooks and metrics lifecycle tests
- P051: Migrate miscellaneous runtime lifecycle tests

## Results
- R044

## Latest Check
C047

## Bodies
- Problem: problems/P000/children/P004/children/P028/children/P043/children/P047/README.md
- Ticket T043: problems/P000/children/P004/children/P028/children/P043/children/P047/tickets/T043.md
- Result R044: problems/P000/children/P004/children/P028/children/P043/children/P047/results/R044.md
- Check C047: problems/P000/children/P004/children/P028/children/P043/children/P047/checks/C047.md

## Follow-ups
- none
