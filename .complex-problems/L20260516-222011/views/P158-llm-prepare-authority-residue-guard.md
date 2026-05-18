# P158: LLM prepare authority residue guard

Status: done
Parent: P154
Root: P000
Source Ticket: T140 (split)
Source Check: none
Package: problems/P000/children/P003/children/P126/children/P134/children/P143/children/P154/children/P158
Body: problems/P000/children/P003/children/P126/children/P134/children/P143/children/P154/children/P158/README.md
Ticket(s): T143

## Problem
The prepare path needs a guard test so future code cannot reintroduce `context.jsonl`/`read_context` authority without review.

This belongs under `P154` because static/source evidence can regress unless captured in tests.

## Success Criteria
- Existing guard coverage is identified or a new guard is added.
- Guard fails if LLM prepare assembly starts using `read_context`/`context/read` as authority.
- Focused tests pass.

## Subproblems
- none

## Results
- R137

## Latest Check
C151

## Bodies
- Problem: problems/P000/children/P003/children/P126/children/P134/children/P143/children/P154/children/P158/README.md
- Ticket T143: problems/P000/children/P003/children/P126/children/P134/children/P143/children/P154/children/P158/tickets/T143.md
- Result R137: problems/P000/children/P003/children/P126/children/P134/children/P143/children/P154/children/P158/results/R137.md
- Check C151: problems/P000/children/P003/children/P126/children/P134/children/P143/children/P154/children/P158/checks/C151.md

## Follow-ups
- none
