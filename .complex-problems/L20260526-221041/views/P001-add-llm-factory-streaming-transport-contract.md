# P001: Add LLM Factory streaming transport contract

Status: done
Parent: P000
Root: P000
Source Ticket: T000 (split)
Source Check: none
Package: problems/P000/children/P001
Body: problems/P000/children/P001/README.md
Ticket(s): T001

## Problem
LLM Factory currently accepts a `stream` request flag but does not implement streaming provider transport. Reasoning streaming needs Factory to expose a clear, normalized stream for supported providers while preserving the existing non-streaming response path.

## Success Criteria
- Factory has a provider-level streaming contract for OpenAI-compatible chat completions.
- Streaming chunks preserve reasoning/content/tool-call deltas in a normalized shape Runtime can consume.
- Non-streaming chat completions remain compatible and covered by tests.
- Unsupported providers fail clearly rather than silently pretending to stream.

## Subproblems
- P005: Implement OpenAI-compatible streaming chunk normalization
- P006: Wire Factory chat route streaming response and logging

## Results
- R002

## Latest Check
C002

## Bodies
- Problem: problems/P000/children/P001/README.md
- Ticket T001: problems/P000/children/P001/tickets/T001.md
- Result R002: problems/P000/children/P001/results/R002.md
- Check C002: problems/P000/children/P001/checks/C002.md

## Follow-ups
- none
