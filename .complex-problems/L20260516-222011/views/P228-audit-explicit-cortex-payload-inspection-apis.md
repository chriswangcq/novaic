# P228: Audit explicit Cortex payload inspection APIs

Status: done
Parent: P129
Root: P000
Source Ticket: T220 (split)
Source Check: none
Package: problems/P000/children/P003/children/P129/children/P228
Body: problems/P000/children/P003/children/P129/children/P228/README.md
Ticket(s): T221

## Problem
Payload read/search/summarize/qa APIs must be explicit, bounded, and pointer-addressed.

## Success Criteria
- Payload API entrypoints are mapped with file/function pointers.
- Read/search behavior is bounded by explicit mode/limit/query inputs.
- Summarize/qa behavior is classified as explicit payload interpretation, not default context assembly.
- Tests verify bounded retrieval behavior.

## Subproblems
- none

## Results
- R218

## Latest Check
C232

## Bodies
- Problem: problems/P000/children/P003/children/P129/children/P228/README.md
- Ticket T221: problems/P000/children/P003/children/P129/children/P228/tickets/T221.md
- Result R218: problems/P000/children/P003/children/P129/children/P228/results/R218.md
- Check C232: problems/P000/children/P003/children/P129/children/P228/checks/C232.md

## Follow-ups
- none
