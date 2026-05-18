# P260: Agent-runtime current versus historical media regression coverage

Status: done
Parent: P132
Root: P000
Source Ticket: T254 (split)
Source Check: none
Package: problems/P000/children/P003/children/P132/children/P260
Body: problems/P000/children/P003/children/P132/children/P260/README.md
Ticket(s): T259

## Problem
Agent-runtime assembles the LLM context and decides whether display media is current-turn provider media or historical sanitized text. It needs focused tests that prove current display media survives as provider-native media while later history replay does not re-inject raw media payloads.

## Success Criteria
- Focused runtime context tests pass.
- Tests prove current explicit display perception can become provider-native image content.
- Tests prove historical display/tool messages replace image data with placeholders or manifest text.
- Tests prove shell output remains bounded terminal text and does not become display media by content sniffing.

## Subproblems
- P266: Runtime media regression coverage inventory
- P267: Runtime media missing regression implementation
- P268: Runtime media focused verification

## Results
- R259

## Latest Check
C274

## Bodies
- Problem: problems/P000/children/P003/children/P132/children/P260/README.md
- Ticket T259: problems/P000/children/P003/children/P132/children/P260/tickets/T259.md
- Result R259: problems/P000/children/P003/children/P132/children/P260/results/R259.md
- Check C274: problems/P000/children/P003/children/P132/children/P260/checks/C274.md

## Follow-ups
- none
