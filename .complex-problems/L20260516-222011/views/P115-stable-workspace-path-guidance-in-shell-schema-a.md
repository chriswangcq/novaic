# P115: Stable Workspace Path Guidance in Shell Schema and Help

Status: done
Parent: P114
Root: P000
Source Ticket: T108 (split)
Source Check: none
Package: problems/P000/children/P002/children/P103/children/P107/children/P114/children/P115
Body: problems/P000/children/P002/children/P103/children/P107/children/P114/children/P115/README.md
Ticket(s): T109

## Problem
The LLM-facing shell schema and generated Cortex shell help must consistently teach agents to use stable `/cortex/ro`, `/cortex/rw`, `$RO`, and `$RW` paths, and not copied `novaic-cortex-sandbox-*` backing paths.

## Success Criteria
- Inspect canonical shell schema for stable path guidance.
- Inspect generated `cortex --help` and related help text for stable path guidance.
- Fix any missing guidance and add or run focused schema/help guards.
- Confirm no public help text encourages copied `novaic-cortex-sandbox-*` paths.

## Subproblems
- none

## Results
- R104

## Latest Check
C118

## Bodies
- Problem: problems/P000/children/P002/children/P103/children/P107/children/P114/children/P115/README.md
- Ticket T109: problems/P000/children/P002/children/P103/children/P107/children/P114/children/P115/tickets/T109.md
- Result R104: problems/P000/children/P002/children/P103/children/P107/children/P114/children/P115/results/R104.md
- Check C118: problems/P000/children/P002/children/P103/children/P107/children/P114/children/P115/checks/C118.md

## Follow-ups
- none
