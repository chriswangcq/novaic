# P157: Runtime LLM prepare caller authority

Status: done
Parent: P154
Root: P000
Source Ticket: T140 (split)
Source Check: none
Package: problems/P000/children/P003/children/P126/children/P134/children/P143/children/P154/children/P157
Body: problems/P000/children/P003/children/P126/children/P134/children/P143/children/P154/children/P157/README.md
Ticket(s): T142

## Problem
Runtime LLM call assembly must invoke Cortex prepare/read-model APIs rather than `context/read` projection APIs when constructing provider messages.

This belongs under `P154` because even a correct Cortex endpoint is insufficient if runtime calls a different legacy API.

## Success Criteria
- Runtime prepare-context caller and LLM assembly path are mapped.
- Evidence proves runtime uses `/v1/context/prepare_for_llm` or the explicit prepare contract.
- Evidence proves runtime LLM assembly does not call `read_context` as authority.

## Subproblems
- none

## Results
- R136

## Latest Check
C150

## Bodies
- Problem: problems/P000/children/P003/children/P126/children/P134/children/P143/children/P154/children/P157/README.md
- Ticket T142: problems/P000/children/P003/children/P126/children/P134/children/P143/children/P154/children/P157/tickets/T142.md
- Result R136: problems/P000/children/P003/children/P126/children/P134/children/P143/children/P154/children/P157/results/R136.md
- Check C150: problems/P000/children/P003/children/P126/children/P134/children/P143/children/P154/children/P157/checks/C150.md

## Follow-ups
- none
