# P016: Ephemeral path and media payload leakage scan

Status: done
Parent: P009
Root: P000
Source Ticket: T008 (split)
Source Check: none
Package: problems/P000/children/P001/children/P009/children/P016
Body: problems/P000/children/P001/children/P009/children/P016/README.md
Ticket(s): T039

## Problem
Search for active code paths that leak ephemeral `/tmp/novaic-cortex-sandbox-*` backing paths, base64 screenshots/media as text, or generic image injection into LLM context.

## Success Criteria
- Active code/tests are searched for ephemeral path, base64/image leakage, screenshot payload, and projection keywords.
- Hits are triaged into current guard, benign test fixture, or active issue.
- Any active leakage path is fixed or routed to the relevant specialized child problem.
- Targeted tests protect the intended pointer/blob/display contract.

## Subproblems
- P047: Ephemeral Cortex backing path residue
- P048: Media/base64 tool output contract
- P049: Docs and examples for file/blob output contract

## Results
- R055

## Latest Check
C067

## Bodies
- Problem: problems/P000/children/P001/children/P009/children/P016/README.md
- Ticket T039: problems/P000/children/P001/children/P009/children/P016/tickets/T039.md
- Result R055: problems/P000/children/P001/children/P009/children/P016/results/R055.md
- Check C067: problems/P000/children/P001/children/P009/children/P016/checks/C067.md

## Follow-ups
- none
