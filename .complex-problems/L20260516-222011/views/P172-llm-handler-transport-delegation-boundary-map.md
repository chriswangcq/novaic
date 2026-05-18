# P172: LLM handler transport delegation boundary map

Status: done
Parent: P169
Root: P000
Source Ticket: T155 (split)
Source Check: none
Package: problems/P000/children/P003/children/P126/children/P135/children/P161/children/P169/children/P172
Body: problems/P000/children/P003/children/P126/children/P135/children/P161/children/P169/children/P172/README.md
Ticket(s): T157

## Problem
`handlers/llm_handlers.py` should delegate payload parsing and provider preparation to explicit contract code, then call the LLM business transport. It must not read Cortex context or reconstruct provider messages directly.

## Success Criteria
- `llm_handlers.py` is mapped for `LLMCallInput.from_payload`, `prepare_llm_call`, and final transport call.
- Static or behavioral tests prove handler code does not call `read_context` or `context.read`.
- Focused handler tests are run.
- Any direct provider-message reconstruction in the handler is fixed or split.

## Subproblems
- none

## Results
- R151

## Latest Check
C165

## Bodies
- Problem: problems/P000/children/P003/children/P126/children/P135/children/P161/children/P169/children/P172/README.md
- Ticket T157: problems/P000/children/P003/children/P126/children/P135/children/P161/children/P169/children/P172/tickets/T157.md
- Result R151: problems/P000/children/P003/children/P126/children/P135/children/P161/children/P169/children/P172/results/R151.md
- Check C165: problems/P000/children/P003/children/P126/children/P135/children/P161/children/P169/children/P172/checks/C165.md

## Follow-ups
- none
