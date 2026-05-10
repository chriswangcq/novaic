# P003: Phase 2: Context projections and replay

Status: done
Parent: P000
Root: P000
Package: problems/P000/children/P003
Body: problems/P000/children/P003/README.md
Ticket(s): T010

## Problem
Implement projections from the context event stream to LLM context state and workspace-compatible views. This includes folded summaries, active stack, tool observations, notification hints, and replay/repair behavior.

## Success Criteria
- A pure replay/projector can derive prepared LLM messages and active stack from events.
- Projection handles wake start, system prompt, notification hint, assistant message, tool step, skill begin, skill end, and wake archive events.
- Projection output is generation-checked and can be rebuilt from event stream.
- Tests cover fold behavior, nested skills, stale open sibling suppression, tool result placement, and notification hint semantics.

## Subproblems
- P014: Phase 2.1: Projection snapshot and message events
- P015: Phase 2.2: Projection scope stack and fold semantics
- P016: Phase 2.3: Projection tool call/result placement
- P017: Phase 2.4: Projection verification and non-cutover audit
- P022: Add projection replay watermark and sequence validation

## Results
- R017

## Latest Check
C020

## Bodies
- Problem: problems/P000/children/P003/README.md
- Ticket T010: problems/P000/children/P003/tickets/T010.md
- Result R017: problems/P000/children/P003/results/R017.md
- Check C018: problems/P000/children/P003/checks/C018.md
- Check C020: problems/P000/children/P003/checks/C020.md

## Follow-ups
- P022: Add projection replay watermark and sequence validation
