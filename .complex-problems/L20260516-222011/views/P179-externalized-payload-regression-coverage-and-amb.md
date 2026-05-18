# P179: Externalized payload regression coverage and ambiguity cleanup

Status: done
Parent: P136
Root: P000
Source Ticket: T164 (split)
Source Check: none
Package: problems/P000/children/P003/children/P126/children/P136/children/P179
Body: problems/P000/children/P003/children/P126/children/P136/children/P179/README.md
Ticket(s): T168

## Problem
Even if individual layers look correct, regression coverage must prove externalized/blob-like payload refs do not break stable step lookup, do not leak raw payloads into public context, and do not leave compatibility branches that silently treat `step_ref` and `payload_ref` as interchangeable.

## Success Criteria
- Inventory tests covering externalized payload refs, artifact refs, public truncation, and display/media projection.
- Add missing tests that fail if `step_ref` and `payload_ref` are conflated.
- Classify any compatibility or legacy branches as active, dead, or stale; remove/fix stale branches where in scope.
- Run the selected focused runtime and Cortex tests after changes.

## Subproblems
- none

## Results
- R164

## Latest Check
C178

## Bodies
- Problem: problems/P000/children/P003/children/P126/children/P136/children/P179/README.md
- Ticket T168: problems/P000/children/P003/children/P126/children/P136/children/P179/tickets/T168.md
- Result R164: problems/P000/children/P003/children/P126/children/P136/children/P179/results/R164.md
- Check C178: problems/P000/children/P003/children/P126/children/P136/children/P179/checks/C178.md

## Follow-ups
- none
