# P041: Phase 4A Payload Manifest Boundary Audit

Status: done
Parent: P005
Root: P000
Package: problems/P000/children/P005/children/P041
Body: problems/P000/children/P005/children/P041/README.md
Ticket(s): T040

## Problem
Before wiring manifests, the current payload authority paths need a precise audit. `Workspace.write_payload`, `Workspace.read_payload`, step normalization, Blob adapter behavior, existing `OperationalSqliteStore` manifest methods, and tests must be mapped so implementation does not accidentally leave BlobRef as hidden semantic authority.

## Success Criteria
- All live payload write/read/externalization call sites are cataloged.
- Existing `payload_manifest` table/API fields are compared against the required semantic manifest contract.
- Local JSON payload behavior and external Blob payload behavior are classified separately.
- Missing/corrupt/fetch-failure behavior is identified with concrete current exceptions.
- Follow-on implementation child problems have explicit boundaries and no ambiguous payload authority source remains unclassified.

## Subproblems
- none

## Results
- R038

## Latest Check
C041

## Bodies
- Problem: problems/P000/children/P005/children/P041/README.md
- Ticket T040: problems/P000/children/P005/children/P041/tickets/T040.md
- Result R038: problems/P000/children/P005/children/P041/results/R038.md
- Check C041: problems/P000/children/P005/children/P041/checks/C041.md

## Follow-ups
- none
