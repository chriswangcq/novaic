# P007: Phase 1.1: Define ContextEvent schema and validation

Status: done
Parent: P002
Root: P000
Package: problems/P000/children/P002/children/P007
Body: problems/P000/children/P002/children/P007/README.md
Ticket(s): T003

## Problem
Create the deterministic ContextEvent domain model for Cortex. This belongs under Phase 1 because append/read storage cannot be trustworthy until the event envelope, valid event types, canonical semantic body, and validation errors are explicit.

## Success Criteria
- ContextEvent envelope fields are represented in code with explicit schema version, event id, stream id, root scope id, sequence, idempotency key, occurred_at, actor, type, payload, and optional generation/version data if needed.
- Valid event types match the Phase 0 design document closely enough for later write/read cutover.
- Validation rejects malformed event types, non-object payloads, invalid stream/root identity, non-positive sequence, and missing required fields.
- Canonical semantic body comparison is deterministic and excludes generated fields that should not affect idempotency checks.
- Unit tests cover valid event creation, malformed events, canonical body equality, and deterministic serialization.

## Subproblems
- P011: Strengthen ContextEvent stream identity validation

## Results
- R001

## Latest Check
C003

## Bodies
- Problem: problems/P000/children/P002/children/P007/README.md
- Ticket T003: problems/P000/children/P002/children/P007/tickets/T003.md
- Result R001: problems/P000/children/P002/children/P007/results/R001.md
- Check C001: problems/P000/children/P002/children/P007/checks/C001.md
- Check C003: problems/P000/children/P002/children/P007/checks/C003.md

## Follow-ups
- P011: Strengthen ContextEvent stream identity validation
