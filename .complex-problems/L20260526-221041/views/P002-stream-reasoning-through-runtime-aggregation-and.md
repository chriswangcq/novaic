# P002: Stream reasoning through Runtime aggregation and activity projection

Status: done
Parent: P000
Root: P000
Source Ticket: T000 (split)
Source Check: none
Package: problems/P000/children/P002
Body: problems/P000/children/P002/README.md
Ticket(s): T004

## Problem
Runtime currently waits for a complete Factory response, then projects reasoning once during context append. It needs to consume Factory streaming output, aggregate the final response for saga compatibility, and emit bounded running/final reasoning updates through existing Agent Monitor projection entities.

## Success Criteria
- Runtime can request and consume streaming chat completions from Factory.
- Runtime returns a complete OpenAI-style response to existing saga decision code.
- Runtime emits stable same-record reasoning updates with `status=running` and a final completed state.
- Projection writes are coalesced/bounded and do not write one row per token.
- Durable context append semantics remain final-response only.

## Subproblems
- P007: Add Runtime Factory stream parser and final response aggregator
- P008: Add stable running reasoning activity projection updates
- P009: Integrate streaming LLM calls into Runtime handler

## Results
- R006

## Latest Check
C006

## Bodies
- Problem: problems/P000/children/P002/README.md
- Ticket T004: problems/P000/children/P002/tickets/T004.md
- Result R006: problems/P000/children/P002/results/R006.md
- Check C006: problems/P000/children/P002/checks/C006.md

## Follow-ups
- none
