# P001: Add structured public title to activity projection contract and runtime

Status: done
Parent: P000
Root: P000
Source Ticket: T000 (split)
Source Check: none
Package: problems/P000/children/P001
Body: problems/P000/children/P001/README.md
Ticket(s): T001

## Problem
The runtime currently emits `agent-activity-records` with generic `title` and private/detail `text`, while the frontend invents some public titles by reading reasoning text. The durable projection contract needs an explicit public presentation field so monitor row titles are data, not UI keyword guesses.

## Success Criteria
- Shared/app entity contract for `agent-activity-records` includes `public_title`.
- Business schema for `agent_activity_records` includes `public_title` when schema push definitions are used.
- Runtime `activity_projection` emits `public_title` for reasoning, tool calls, tool observations, and scope summaries.
- Runtime projection tests verify `public_title` exists and carries expected user-facing values.
- Existing runtime behavior for reasoning detail text and shell desc text remains intact.

## Subproblems
- none

## Results
- R000

## Latest Check
C000

## Bodies
- Problem: problems/P000/children/P001/README.md
- Ticket T001: problems/P000/children/P001/tickets/T001.md
- Result R000: problems/P000/children/P001/results/R000.md
- Check C000: problems/P000/children/P001/checks/C000.md

## Follow-ups
- none
