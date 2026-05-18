# P414: Cortex handler and bridge residue classification

Status: done
Parent: P409
Root: P000
Source Ticket: T398 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P403/children/P409/children/P414
Body: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P403/children/P409/children/P414/README.md
Ticket(s): T401

## Problem
`cortex_handlers.py` and `cortex_bridge.py` contain round/counter/archive hits around Cortex scope archive and context event APIs. They must be classified so Cortex bridge counters do not hide session identity fallback.

## Success Criteria
- Inspect Cortex handler and bridge guard hits.
- Confirm session generation is explicit at scope-end/archive boundaries.
- Classify `round_num` and Cortex counter defaults as non-session counters where safe.
- Patch and test any session identity fallback.
- Run focused Cortex handler/bridge tests.

## Subproblems
- none

## Results
- R394

## Latest Check
C420

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P403/children/P409/children/P414/README.md
- Ticket T401: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P403/children/P409/children/P414/tickets/T401.md
- Result R394: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P403/children/P409/children/P414/results/R394.md
- Check C420: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P403/children/P409/children/P414/checks/C420.md

## Follow-ups
- none
