# P139: ContextEvent pure projection map

Status: done
Parent: P133
Root: P000
Source Ticket: T123 (split)
Source Check: none
Package: problems/P000/children/P003/children/P126/children/P133/children/P139
Body: problems/P000/children/P003/children/P126/children/P133/children/P139/README.md
Ticket(s): T125

## Problem
`project_context_events` transforms ordered events into LLM-facing messages and stack. Its event handlers must be mapped so later projection work does not violate LIFO, folded summaries, tool result ordering, or notification behavior.

## Success Criteria
- Projection invariants for stream/root/sequence validation are documented.
- Event handlers for wake, skill, system, context messages, notifications, assistant tool calls, and tool results are mapped.
- The roles of `step_ref`, `payload_ref`, orphan tool result marking, and folded summary messages are documented.
- Projection tests are run and any active issue is fixed or split.

## Subproblems
- none

## Results
- R121

## Latest Check
C135

## Bodies
- Problem: problems/P000/children/P003/children/P126/children/P133/children/P139/README.md
- Ticket T125: problems/P000/children/P003/children/P126/children/P133/children/P139/tickets/T125.md
- Result R121: problems/P000/children/P003/children/P126/children/P133/children/P139/results/R121.md
- Check C135: problems/P000/children/P003/children/P126/children/P133/children/P139/checks/C135.md

## Follow-ups
- none
