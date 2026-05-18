# P212: Audit generic dict JSON fallback projection branch

Status: done
Parent: P209
Root: P000
Source Ticket: T198 (split)
Source Check: none
Package: problems/P000/children/P003/children/P127/children/P187/children/P199/children/P209/children/P212
Body: problems/P000/children/P003/children/P127/children/P187/children/P199/children/P209/children/P212/README.md
Ticket(s): T201

## Problem
`parse_tool_result` falls back to JSON serialization for unknown dict payloads. This may be useful for diagnostics or may hide stale unstructured contracts. Decide whether to retain, narrow, or remove it.

## Success Criteria
- The fallback has a documented safety reason or is replaced by a narrower projection.
- Unknown dict handling cannot silently become media/image injection.
- Tests cover retained or changed behavior.

## Subproblems
- none

## Results
- R195

## Latest Check
C209

## Bodies
- Problem: problems/P000/children/P003/children/P127/children/P187/children/P199/children/P209/children/P212/README.md
- Ticket T201: problems/P000/children/P003/children/P127/children/P187/children/P199/children/P209/children/P212/tickets/T201.md
- Result R195: problems/P000/children/P003/children/P127/children/P187/children/P199/children/P209/children/P212/results/R195.md
- Check C209: problems/P000/children/P003/children/P127/children/P187/children/P199/children/P209/children/P212/checks/C209.md

## Follow-ups
- none
