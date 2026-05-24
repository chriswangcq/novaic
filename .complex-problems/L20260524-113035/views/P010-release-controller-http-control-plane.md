# P010: Release-controller HTTP control plane

Status: done
Parent: P002
Root: P000
Source Ticket: T002 (split)
Source Check: none
Package: problems/P000/children/P002/children/P010
Body: problems/P000/children/P002/children/P010/README.md
Ticket(s): T006

## Problem
Expose the release-controller core through a small HTTP API for health, status, rules, run inspection, manual branch triggers, prod promotion, and namespace rollback.

This belongs under P002 because operators and later deployment automation need a central API surface rather than shelling into the host for release actions.

## Success Criteria
- `/health` returns a minimal health response.
- `/v1/status` reports controller state directory, known branch heads, current pointers, previous pointers, candidates, and recent runs.
- `/v1/rules` returns configured branch rules.
- `/v1/runs` and `/v1/runs/{run_id}` expose persisted run records.
- `/v1/triggers` starts or dry-runs a branch release plan through the shared planner.
- `/v1/promotions/prod` promotes immutable image refs to prod only through explicit API input.
- `/v1/rollbacks/{namespace}` rolls back from recorded previous pointers or reports a clear error when no previous pointer exists.

## Subproblems
- none

## Results
- R004

## Latest Check
C004

## Bodies
- Problem: problems/P000/children/P002/children/P010/README.md
- Ticket T006: problems/P000/children/P002/children/P010/tickets/T006.md
- Result R004: problems/P000/children/P002/children/P010/results/R004.md
- Check C004: problems/P000/children/P002/children/P010/checks/C004.md

## Follow-ups
- none
