# P078: Add Queue Postgres JSON Expression Indexes

Status: done
Parent: P073
Root: P000
Source Ticket: none (none)
Source Check: C075
Package: problems/P000/children/P024/children/P028/children/P073/children/P078
Body: problems/P000/children/P024/children/P028/children/P073/children/P078/README.md
Ticket(s): T074

## Problem
P073 added the Queue Postgres schema and database boundary, but the schema is missing the two required JSONB expression indexes from the Queue PG design artifacts. Without them, the schema does not fully satisfy the original index-family success criteria for first-cutover Postgres behavior.

## Success Criteria
- `POSTGRES_SCHEMA_STATEMENTS` includes `idx_tq_tasks_payload_agent` on `tq_tasks ((payload ->> 'agent_id')) WHERE payload ? 'agent_id'`.
- `POSTGRES_SCHEMA_STATEMENTS` includes `idx_tq_saga_state_context_agent` on `tq_saga_state ((context ->> 'agent_id')) WHERE context ? 'agent_id'`.
- Focused tests assert both JSON expression indexes and still pass with the existing Queue Postgres boundary test suite.

## Subproblems
- none

## Results
- R072

## Latest Check
C076

## Bodies
- Problem: problems/P000/children/P024/children/P028/children/P073/children/P078/README.md
- Ticket T074: problems/P000/children/P024/children/P028/children/P073/children/P078/tickets/T074.md
- Result R072: problems/P000/children/P024/children/P028/children/P073/children/P078/results/R072.md
- Check C076: problems/P000/children/P024/children/P028/children/P073/children/P078/checks/C076.md

## Follow-ups
- none
