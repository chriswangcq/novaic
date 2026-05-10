# P001: Phase 0: Event-sourced context design and construction plan

Status: done
Parent: P000
Root: P000
Package: problems/P000/children/P001
Body: problems/P000/children/P001/README.md
Ticket(s): T001

## Problem
Write the final design document and construction plan for the full Cortex event-sourced context source model. The document must define source events, stream identity, ordering, idempotency, projections, old-data deletion policy, and cutover invariants before implementation begins.

## Success Criteria
- A repo design document exists with final architecture, event schema, projection model, and migration/no-compat policy.
- The document names exact current paths to delete or demote from source-of-truth to projection.
- The document defines implementation phases and strict checks for each phase.
- The design avoids permanent dual truth and explains how old data reset works.

## Subproblems
- none

## Results
- R000

## Latest Check
C000

## Bodies
- Problem: problems/P000/children/P001/README.md
- Ticket T001: problems/P000/children/P001/tickets/T001.md
- Result R000: problems/P000/children/P001/results/R000.md
- Check C000: problems/P000/children/P001/checks/C000.md

## Follow-ups
- none
