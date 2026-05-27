# P005: Implement OpenAI-compatible streaming chunk normalization

Status: done
Parent: P001
Root: P000
Source Ticket: T001 (split)
Source Check: none
Package: problems/P000/children/P001/children/P005
Body: problems/P000/children/P001/children/P005/README.md
Ticket(s): T002

## Problem
Factory providers need a small, testable contract that turns OpenAI-compatible SSE chat completion chunks into normalized Python dictionaries preserving content, reasoning, tool-call deltas, finish reason, and usage where available.

## Success Criteria
- `OpenAIProvider` exposes a streaming method for OpenAI-compatible chat completions.
- The parser handles `data: {...}` SSE lines and `[DONE]` termination.
- Reasoning deltas are extracted from common fields such as `reasoning_content`, `reasoning`, and provider-specific delta aliases.
- Unit tests cover content, reasoning, tool-call delta, done, and error classification behavior.

## Subproblems
- none

## Results
- R000

## Latest Check
C000

## Bodies
- Problem: problems/P000/children/P001/children/P005/README.md
- Ticket T002: problems/P000/children/P001/children/P005/tickets/T002.md
- Result R000: problems/P000/children/P001/children/P005/results/R000.md
- Check C000: problems/P000/children/P001/children/P005/checks/C000.md

## Follow-ups
- none
