# P156: Cortex prepare_for_llm read model authority

Status: done
Parent: P154
Root: P000
Source Ticket: T140 (split)
Source Check: none
Package: problems/P000/children/P003/children/P126/children/P134/children/P143/children/P154/children/P156
Body: problems/P000/children/P003/children/P126/children/P134/children/P143/children/P154/children/P156/README.md
Ticket(s): T141

## Problem
The Cortex `/v1/context/prepare_for_llm` endpoint must assemble context from the ContextEvent read model, not from `context.jsonl`.

This belongs under `P154` because it is the service-side authority boundary for model context.

## Success Criteria
- Endpoint and helper source path are mapped.
- Evidence proves `prepare_context`/read-model is used.
- Evidence proves `read_context` is not called by the endpoint.

## Subproblems
- none

## Results
- R135

## Latest Check
C149

## Bodies
- Problem: problems/P000/children/P003/children/P126/children/P134/children/P143/children/P154/children/P156/README.md
- Ticket T141: problems/P000/children/P003/children/P126/children/P134/children/P143/children/P154/children/P156/tickets/T141.md
- Result R135: problems/P000/children/P003/children/P126/children/P134/children/P143/children/P154/children/P156/results/R135.md
- Check C149: problems/P000/children/P003/children/P126/children/P134/children/P143/children/P154/children/P156/checks/C149.md

## Follow-ups
- none
