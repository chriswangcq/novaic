# P000: Cortex incremental LLM context assembly research

Status: done
Parent: none
Root: P000
Package: problems/P000
Body: problems/P000/README.md
Ticket(s): T000

## Problem
Research the current novaic-cortex LLM context assembly implementation and evaluate whether context can be assembled before the LLM call or maintained incrementally instead of rebuilding from DFS state only during `prepare_for_llm`.

## Success Criteria
- Identify the current call-time assembly path and the write events that mutate context state.
- Explain why the current implementation assembles on demand and where the cost/latency comes from.
- Provide multiple design options for non-call-time or incremental assembly.
- Compare each option by correctness, latency, complexity, recovery behavior, and fit with the Cortex/agent subject model.
- Recommend a direction and name residual risks without starting implementation.

## Subproblems
- none

## Results
- R000

## Latest Check
C000

## Bodies
- Problem: problems/P000/README.md
- Ticket T000: problems/P000/tickets/T000.md
- Result R000: problems/P000/results/R000.md
- Check C000: problems/P000/checks/C000.md

## Follow-ups
- none
