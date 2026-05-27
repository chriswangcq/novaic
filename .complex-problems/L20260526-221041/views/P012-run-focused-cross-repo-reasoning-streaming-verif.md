# P012: Run focused cross-repo reasoning streaming verification

Status: done
Parent: P004
Root: P000
Source Ticket: T011 (split)
Source Check: none
Package: problems/P000/children/P004/children/P012
Body: problems/P000/children/P004/children/P012/README.md
Ticket(s): T012

## Problem
The streaming path touches Factory, Runtime, and App. The final pass needs concrete test evidence across all touched repos, including Factory SSE, Runtime aggregation/projection/handler integration, and App timeline/contract behavior.

## Success Criteria
- Focused tests pass in `novaic-llm-factory` for streaming chat route/provider behavior.
- Focused tests pass in `novaic-agent-runtime` for Factory stream parsing, activity projection, and LLM handler integration.
- Focused tests pass in `novaic-app` for ActivityTimeline, hook normalization, entity contract, and guard behavior.
- Any failure is recorded with exact command output and either fixed or escalated as a follow-up.

## Subproblems
- none

## Results
- R010

## Latest Check
C010

## Bodies
- Problem: problems/P000/children/P004/children/P012/README.md
- Ticket T012: problems/P000/children/P004/children/P012/tickets/T012.md
- Result R010: problems/P000/children/P004/children/P012/results/R010.md
- Check C010: problems/P000/children/P004/children/P012/checks/C010.md

## Follow-ups
- none
