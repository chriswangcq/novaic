# P033: Phase 3.3.2: Wire context append and batch endpoints to events

Status: done
Parent: P025
Root: P000
Package: problems/P000/children/P004/children/P025/children/P033
Body: problems/P000/children/P004/children/P025/children/P033/README.md
Ticket(s): T028

## Problem
After the idempotency contract is explicit, `/v1/context/append` and `/v1/context/batch` must append ContextEvents as authoritative facts before transitional legacy context writes.

## Success Criteria
- `context_append` appends one event for the message.
- `context_batch` appends ordered events for every message.
- Assistant messages with tool calls are recorded as `AssistantToolCallRecorded`; other messages are recorded as `ContextMessageAppended`.
- Tests verify event order and payload shape.
- Existing legacy context behavior remains green until read-path cutover.

## Subproblems
- none

## Results
- R025

## Latest Check
C027

## Bodies
- Problem: problems/P000/children/P004/children/P025/children/P033/README.md
- Ticket T028: problems/P000/children/P004/children/P025/children/P033/tickets/T028.md
- Result R025: problems/P000/children/P004/children/P025/children/P033/results/R025.md
- Check C027: problems/P000/children/P004/children/P025/children/P033/checks/C027.md

## Follow-ups
- none
