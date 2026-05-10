# P025: Phase 3.3: Cut context append and batch writes to events

Status: done
Parent: P004
Root: P000
Package: problems/P000/children/P004/children/P025
Body: problems/P000/children/P004/children/P025/README.md
Ticket(s): T026

## Problem
`context.append` and `context.batch` currently write source context rows directly to legacy `context.jsonl`. They must append event facts first and leave any legacy file output as projection/debug only.

## Success Criteria
- `context.append` appends `ContextMessageAppended` events.
- `context.batch` appends one deterministic event per message or an explicitly modeled batch event if the event schema is extended.
- Tests verify event order, idempotency/retry behavior, and event payload shape.
- No old direct `context.jsonl` write remains as source-of-truth behavior.

## Subproblems
- P032: Phase 3.3.1: Define context message event idempotency contract
- P033: Phase 3.3.2: Wire context append and batch endpoints to events
- P034: Phase 3.3.3: Verify context append/batch cutover boundaries

## Results
- R027

## Latest Check
C029

## Bodies
- Problem: problems/P000/children/P004/children/P025/README.md
- Ticket T026: problems/P000/children/P004/children/P025/tickets/T026.md
- Result R027: problems/P000/children/P004/children/P025/results/R027.md
- Check C029: problems/P000/children/P004/children/P025/checks/C029.md

## Follow-ups
- none
