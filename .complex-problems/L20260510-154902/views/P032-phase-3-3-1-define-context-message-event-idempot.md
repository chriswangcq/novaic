# P032: Phase 3.3.1: Define context message event idempotency contract

Status: done
Parent: P025
Root: P000
Package: problems/P000/children/P004/children/P025/children/P032
Body: problems/P000/children/P004/children/P025/children/P032/README.md
Ticket(s): T027

## Problem
Context append/batch needs event idempotency without collapsing legitimately repeated identical messages. The request contract must be explicit before endpoint cutover.

## Success Criteria
- `ContextAppendRequest` and `ContextBatchRequest` support optional explicit event idempotency keys.
- Missing keys remain backward-compatible and append distinct events.
- Supplied keys are passed through to ContextEventStore.
- Tests prove same-content messages with different/no keys remain distinct, while retry with the same key dedupes.

## Subproblems
- none

## Results
- R024

## Latest Check
C026

## Bodies
- Problem: problems/P000/children/P004/children/P025/children/P032/README.md
- Ticket T027: problems/P000/children/P004/children/P025/children/P032/tickets/T027.md
- Result R024: problems/P000/children/P004/children/P025/children/P032/results/R024.md
- Check C026: problems/P000/children/P004/children/P025/children/P032/checks/C026.md

## Follow-ups
- none
