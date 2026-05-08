# P002: Old Path And Compatibility Residue Scan

Status: done
Parent: P000
Root: P000
Package: problems/P000/children/P002
Body: problems/P000/children/P002/README.md
Ticket(s): T002

## Problem
Audit the runtime worker/action/handler source surface for old paths that could bypass the new FSM/worker/DSL boundaries: direct effect execution in action engines, handler-owned lifecycle wiring, bespoke worker loops, compatibility branches, or stale no-generation/fallback behavior.

## Success Criteria
- Source scans cover action engines, handlers, worker assemblies, worker entrypoints, and Queue Service session/FSM surfaces.
- Findings distinguish accepted explicit boundaries from active old-path residue.
- No direct action-engine `execute_effect(...)`, handler lifecycle ownership, or displaced bespoke loop remains unguarded.
- Any real residue is fixed or converted into a follow-up problem.

## Subproblems
- none

## Results
- R001

## Latest Check
C001

## Bodies
- Problem: problems/P000/children/P002/README.md
- Ticket T002: problems/P000/children/P002/tickets/T002.md
- Result R001: problems/P000/children/P002/results/R001.md
- Check C001: problems/P000/children/P002/checks/C001.md

## Follow-ups
- none
