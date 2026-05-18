# P176: Runtime tool result wrapper ref contract

Status: done
Parent: P136
Root: P000
Source Ticket: T164 (split)
Source Check: none
Package: problems/P000/children/P003/children/P126/children/P136/children/P176
Body: problems/P000/children/P003/children/P126/children/P136/children/P176/README.md
Ticket(s): T165

## Problem
Runtime tool handlers wrap raw tool output before writing step results and exposing public context. This wrapper layer must clearly emit stable `step_ref`, correct `payload_ref`, durable payload metadata, public text, and artifact refs without leaking large payloads or conflating lookup identity with storage identity.

## Success Criteria
- Map runtime wrapper code that constructs tool result dictionaries, public content, durable payloads, artifacts, `step_ref`, and `payload_ref`.
- Document which fields are public context fields versus durable/raw payload fields.
- Add or tighten focused tests if wrapper behavior permits ref ambiguity or raw payload leakage.
- State whether this layer needs code changes or is already correct.

## Subproblems
- none

## Results
- R161

## Latest Check
C175

## Bodies
- Problem: problems/P000/children/P003/children/P126/children/P136/children/P176/README.md
- Ticket T165: problems/P000/children/P003/children/P126/children/P136/children/P176/tickets/T165.md
- Result R161: problems/P000/children/P003/children/P126/children/P136/children/P176/results/R161.md
- Check C175: problems/P000/children/P003/children/P126/children/P136/children/P176/checks/C175.md

## Follow-ups
- none
