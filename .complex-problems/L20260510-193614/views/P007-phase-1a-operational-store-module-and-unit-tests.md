# P007: Phase 1A Operational Store Module And Unit Tests

Status: done
Parent: P002
Root: P000
Package: problems/P000/children/P002/children/P007
Body: problems/P000/children/P002/children/P007/README.md
Ticket(s): T003

## Problem
Create the Cortex-owned SQLite operational store as a reusable substrate with explicit dependencies and deterministic behavior. This child problem owns the module API, schema creation, and direct unit tests. It must not migrate existing active-stack or scope-transition behavior yet.

## Success Criteria
- Add or finish `novaic_cortex.operational_store` with explicit SQLite path, clock, and ID provider.
- Reject memory-only fallback and avoid hidden env/time/id inputs inside tested behavior.
- Create schema tables for `scope_events`, `scope_projection`, `active_stack_projection`, and `payload_manifest`.
- Add direct unit tests for initialization, append/read, idempotency conflict behavior, projection read/write, active stack read/write, and payload manifest read/write.

## Subproblems
- none

## Results
- R001

## Latest Check
C001

## Bodies
- Problem: problems/P000/children/P002/children/P007/README.md
- Ticket T003: problems/P000/children/P002/children/P007/tickets/T003.md
- Result R001: problems/P000/children/P002/children/P007/results/R001.md
- Check C001: problems/P000/children/P002/children/P007/checks/C001.md

## Follow-ups
- none
