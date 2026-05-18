# P136: Tool result step_ref and payload_ref map

Status: done
Parent: P126
Root: P000
Source Ticket: T122 (split)
Source Check: none
Package: problems/P000/children/P003/children/P126/children/P136
Body: problems/P000/children/P003/children/P126/children/P136/README.md
Ticket(s): T164

## Problem
Tool results flow through runtime handlers into Cortex step and ContextEvent projections. The join keys `step_ref` and `payload_ref` must be stable and correctly distinguished, especially when payloads are externalized to blob references.

## Success Criteria
- Runtime tool result creation paths and Cortex projection handling of `step_ref`/`payload_ref` are mapped.
- The contract for stable `step_ref` versus actual/externalized `payload_ref` is documented.
- Tests prove externalized payloads keep stable step lookup refs while recording blob payload refs.
- Any ambiguous or duplicate key handling is fixed or split into a focused follow-up.

## Subproblems
- P176: Runtime tool result wrapper ref contract
- P177: Cortex step storage and projection ref contract
- P178: Formatted step read and display projection ref contract
- P179: Externalized payload regression coverage and ambiguity cleanup

## Results
- R165

## Latest Check
C179

## Bodies
- Problem: problems/P000/children/P003/children/P126/children/P136/README.md
- Ticket T164: problems/P000/children/P003/children/P126/children/P136/tickets/T164.md
- Result R165: problems/P000/children/P003/children/P126/children/P136/results/R165.md
- Check C179: problems/P000/children/P003/children/P126/children/P136/checks/C179.md

## Follow-ups
- none
