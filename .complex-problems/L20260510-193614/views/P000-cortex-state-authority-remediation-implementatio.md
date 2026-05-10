# P000: Cortex State Authority Remediation Implementation

Status: done
Parent: none
Root: P000
Package: problems/P000
Body: problems/P000/README.md
Ticket(s): T000

## Problem
Implement the remediation plan from `L20260510-192637` in phases rather than leaving it as architecture prose. The implementation should move Cortex control state toward a clean model:

- SQLite for durable operational state and projections.
- LogicalFS/Workspace for file/document authority and trace projection.
- Redis for coordination only.
- Blob for raw bytes with semantic manifests.
- Process memory for cache/config/client wiring only.

Do not attempt a huge one-go rewrite. Design construction first, then implement phase by phase with tests and cleanup.

## Success Criteria
- Create a phased implementation ledger and construction plan.
- Implement at least the first safe phase with tests.
- Each phase must have explicit authority boundary, migration/cleanup, and verification.
- Do not silently keep old runtime paths as active authority after a cutover phase.
- Use strict success checks; if a phase reveals unexpected complexity, split follow-up tickets.

## Subproblems
- P001: Phase 0 Construction Plan And Boundary Map
- P002: Phase 1 Cortex Operational SQLite Store Substrate
- P003: Phase 2 Scope Transition Events To SQLite
- P004: Phase 3 Active Stack And Status SQLite Cutover
- P005: Phase 4 Blob Payload Manifest
- P006: Phase 5 Cleanup And Residue Removal

## Results
- R067

## Latest Check
C071

## Bodies
- Problem: problems/P000/README.md
- Ticket T000: problems/P000/tickets/T000.md
- Result R067: problems/P000/results/R067.md
- Check C071: problems/P000/checks/C071.md

## Follow-ups
- none
