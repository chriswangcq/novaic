# P171: LLMCall contract provider payload source map

Status: done
Parent: P169
Root: P000
Source Ticket: T155 (split)
Source Check: none
Package: problems/P000/children/P003/children/P126/children/P135/children/P161/children/P169/children/P171
Body: problems/P000/children/P003/children/P126/children/P135/children/P161/children/P169/children/P171/README.md
Ticket(s): T156

## Problem
`contracts/llm_call.py` parses `llm.call` payloads and prepares provider messages/tools. It must not read hidden context or invent messages/tools outside explicit input and injected preprocessing functions.

## Success Criteria
- `LLMCallInput.from_payload` and `prepare_llm_call` are mapped with line pointers.
- The explicit source of `messages` and `tools` in the prepared provider call is documented.
- Tests prove preprocessing is injected and ordered, not hidden inside the business transport.
- Any hidden source of context/messages/tools is fixed or split.

## Subproblems
- none

## Results
- R150

## Latest Check
C164

## Bodies
- Problem: problems/P000/children/P003/children/P126/children/P135/children/P161/children/P169/children/P171/README.md
- Ticket T156: problems/P000/children/P003/children/P126/children/P135/children/P161/children/P169/children/P171/tickets/T156.md
- Result R150: problems/P000/children/P003/children/P126/children/P135/children/P161/children/P169/children/P171/results/R150.md
- Check C164: problems/P000/children/P003/children/P126/children/P135/children/P161/children/P169/children/P171/checks/C164.md

## Follow-ups
- none
