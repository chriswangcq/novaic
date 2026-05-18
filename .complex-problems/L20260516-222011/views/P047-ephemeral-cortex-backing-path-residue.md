# P047: Ephemeral Cortex backing path residue

Status: done
Parent: P016
Root: P000
Source Ticket: T039 (split)
Source Check: none
Package: problems/P000/children/P001/children/P009/children/P016/children/P047
Body: problems/P000/children/P001/children/P009/children/P016/children/P047/README.md
Ticket(s): T040

## Problem
Old outputs and docs may still mention `/tmp/novaic-cortex-sandbox-*` or encourage agents to reuse backing paths instead of `/cortex/ro`, `/cortex/rw`, `$RO`, or `$RW`.

## Success Criteria
- Active docs/prompts/tests do not instruct agents to reuse ephemeral backing paths.
- Any remaining ephemeral path references are historical failure examples or tests, clearly marked.
- Focused scan/classification exists.

## Subproblems
- none

## Results
- R036

## Latest Check
C046

## Bodies
- Problem: problems/P000/children/P001/children/P009/children/P016/children/P047/README.md
- Ticket T040: problems/P000/children/P001/children/P009/children/P016/children/P047/tickets/T040.md
- Result R036: problems/P000/children/P001/children/P009/children/P016/children/P047/results/R036.md
- Check C046: problems/P000/children/P001/children/P009/children/P016/children/P047/checks/C046.md

## Follow-ups
- none
