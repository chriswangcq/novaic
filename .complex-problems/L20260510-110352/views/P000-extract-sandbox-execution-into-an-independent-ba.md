# P000: Extract sandbox execution into an independent base service

Status: done
Parent: none
Root: P000
Package: problems/P000
Body: problems/P000/README.md
Ticket(s): T000

## Problem
The user wants business-agnostic infrastructure capabilities to become independent servers, not only shared modules. The current shell execution still runs inside Cortex: Cortex materializes LogicalFS and directly executes commands through common sandbox primitives in-process.

We need to design and implement a real `sandboxd` service boundary without creating a fake half-migration. The service should own generic execution environment mechanics while Cortex keeps business semantics: Workspace, `/ro`/`/rw`, agent identity, shell capabilities, and Blob mapping.

## Success Criteria
- A service boundary is defined for generic sandbox execution with stable request/response contracts.
- The service does not know Cortex Workspace, Blob, agent, skill, or `/ro`/`/rw` semantics beyond caller-provided mount/env/cwd data.
- Cortex uses a client path to call the service rather than directly running subprocesses when configured.
- Tests cover the service contract, client, and Cortex integration path.
- Local direct runner remains only as an explicitly named test/dev adapter if needed, not as an ambiguous current production path.
- Residue scans make it clear which path is active.

## Subproblems
- P001: Sandboxd common contract and client
- P002: Sandboxd independent service
- P003: Cortex uses sandboxd on the active server path
- P004: Deployment and service registry include sandboxd
- P005: Remove stale in-process sandbox execution residue
- P006: End-to-end verification of sandboxd extraction

## Results
- R006

## Latest Check
C006

## Bodies
- Problem: problems/P000/README.md
- Ticket T000: problems/P000/tickets/T000.md
- Result R006: problems/P000/results/R006.md
- Check C006: problems/P000/checks/C006.md

## Follow-ups
- none
