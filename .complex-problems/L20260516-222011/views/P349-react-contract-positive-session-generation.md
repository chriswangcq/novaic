# P349: React contract positive session generation

Status: done
Parent: P337
Root: P000
Source Ticket: T336 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P349
Body: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P349/README.md
Ticket(s): T338

## Problem
`ReactThinkInput` and `ReactActionsInput` still default missing `session_generation` to `0`, and finalize-trigger builders forward that value into wake-finalize context. Runtime finalize enforcement should require explicit positive session generation at these upstream contract boundaries.

## Success Criteria
- Remove `session_generation: int = 0` and `ctx.get("session_generation") or 0` defaults from react contracts where they feed finalize.
- Missing or non-positive session generation fails before finalize-trigger payload creation.
- Update tests that currently assert default `session_generation=0`.
- Verify valid positive generation still flows into prepare/LLM/finalize payloads.

## Subproblems
- none

## Results
- R332

## Latest Check
C353

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P349/README.md
- Ticket T338: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P349/tickets/T338.md
- Result R332: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P349/results/R332.md
- Check C353: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P349/checks/C353.md

## Follow-ups
- none
