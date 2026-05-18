# P159: Runtime saga prepare-context ordering map

Status: done
Parent: P135
Root: P000
Source Ticket: T146 (split)
Source Check: none
Package: problems/P000/children/P003/children/P126/children/P135/children/P159
Body: problems/P000/children/P003/children/P126/children/P135/children/P159/README.md
Ticket(s): T147

## Problem
The ReAct queue saga decides when `prepare_context` runs relative to message reads, tool result persistence, and `llm.call`. The ordering must be mapped so the final LLM call cannot accidentally use stale state from a previous step or wake.

## Success Criteria
- `novaic-agent-runtime/task_queue/sagas/react_think.py` is mapped for prepare-context step ordering and dependencies.
- The dependency handoff from previous saga result into `llm.call` is documented with source pointers.
- Any ordering branch that can skip prepare-context while still calling the LLM is classified as active-safe, dead, or stale.
- Focused tests or static guards covering prepare-before-LLM ordering are identified or added.

## Subproblems
- P164: ReAct saga prepare-context source ordering map
- P165: ReAct saga prepare-context ordering guard

## Results
- R145

## Latest Check
C159

## Bodies
- Problem: problems/P000/children/P003/children/P126/children/P135/children/P159/README.md
- Ticket T147: problems/P000/children/P003/children/P126/children/P135/children/P159/tickets/T147.md
- Result R145: problems/P000/children/P003/children/P126/children/P135/children/P159/results/R145.md
- Check C159: problems/P000/children/P003/children/P126/children/P135/children/P159/checks/C159.md

## Follow-ups
- none
