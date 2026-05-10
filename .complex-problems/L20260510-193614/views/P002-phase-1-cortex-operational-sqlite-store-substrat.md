# P002: Phase 1 Cortex Operational SQLite Store Substrate

Status: done
Parent: P000
Root: P000
Package: problems/P000/children/P002
Body: problems/P000/children/P002/README.md
Ticket(s): T002

## Problem
Cortex needs a durable operational state substrate before active stack/status and transition logs can move off projection files/local NDJSON.

## Success Criteria
- Add a Cortex-owned SQLite store module with explicit path, clock/id boundaries.
- Create tables for scope events, scope projection, active stack projection, and payload manifest.
- Wire the store through registry/startup without using process memory as authority.
- Add tests for schema initialization, event append, projection upsert/read, idempotency, and manifest basics.

## Subproblems
- P007: Phase 1A Operational Store Module And Unit Tests
- P008: Phase 1B Cortex Service Boundary Wiring
- P009: Phase 1C Phase 1 Verification And Residue Audit

## Results
- R004

## Latest Check
C004

## Bodies
- Problem: problems/P000/children/P002/README.md
- Ticket T002: problems/P000/children/P002/tickets/T002.md
- Result R004: problems/P000/children/P002/results/R004.md
- Check C004: problems/P000/children/P002/checks/C004.md

## Follow-ups
- none
