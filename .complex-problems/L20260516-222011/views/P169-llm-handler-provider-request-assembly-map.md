# P169: LLM handler provider request assembly map

Status: done
Parent: P161
Root: P000
Source Ticket: T153 (split)
Source Check: none
Package: problems/P000/children/P003/children/P126/children/P135/children/P161/children/P169
Body: problems/P000/children/P003/children/P126/children/P135/children/P161/children/P169/README.md
Ticket(s): T155

## Problem
`llm_handlers` and `contracts/llm_call.py` turn the `llm.call` payload into the final provider request. That layer must preserve prepared messages/tools and must not rehydrate provider messages from Cortex projections or other local state.

## Success Criteria
- `novaic-agent-runtime/task_queue/handlers/llm_handlers.py` is mapped around `LLMCallInput.from_payload` and `prepare_llm_call`.
- `novaic-agent-runtime/task_queue/contracts/llm_call.py` is mapped for provider-message/tool assembly.
- Tests or static guards prove final provider request `messages` and `tools` come from the explicit `llm.call` payload.
- Any legacy context source reaching provider messages is fixed or split.

## Subproblems
- P171: LLMCall contract provider payload source map
- P172: LLM handler transport delegation boundary map

## Results
- R152

## Latest Check
C166

## Bodies
- Problem: problems/P000/children/P003/children/P126/children/P135/children/P161/children/P169/README.md
- Ticket T155: problems/P000/children/P003/children/P126/children/P135/children/P161/children/P169/tickets/T155.md
- Result R152: problems/P000/children/P003/children/P126/children/P135/children/P161/children/P169/results/R152.md
- Check C166: problems/P000/children/P003/children/P126/children/P135/children/P161/children/P169/checks/C166.md

## Follow-ups
- none
