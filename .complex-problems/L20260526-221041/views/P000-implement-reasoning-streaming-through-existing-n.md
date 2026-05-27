# P000: Implement reasoning streaming through existing NovAIC infrastructure

Status: done
Parent: none
Root: P000
Source Ticket: none (none)
Source Check: none
Package: problems/P000
Body: problems/P000/README.md
Ticket(s): T000

## Problem
NovAIC currently exposes Agent Monitor reasoning only after the LLM call returns a complete assistant message. The desired product behavior is to stream provider-authored reasoning into the existing Agent Monitor path while preserving the current durable final response semantics. The construction must use the existing LLM Factory, Runtime, Business/Entangled, and App sync infrastructure instead of adding a parallel frontend transport.

The work must be handled with recursive closure and the user's split rule: before depth 3, broad work must be split into child problems; from depth 3 onward, one_go is allowed only when the slice is small, concrete, and directly verifiable.

## Success Criteria
- LLM Factory supports streaming provider output for the current OpenAI-compatible path without breaking non-streaming chat completions.
- Runtime can consume Factory streaming output, aggregate final response state, and emit incremental reasoning updates through the existing Agent Monitor projection path.
- Agent Monitor updates use the existing Business/Entangled/App data plane; no new public WebSocket/SSE frontend channel is introduced.
- Final saga behavior remains compatible: downstream decision/action code receives a complete OpenAI-style chat completion response.
- Streaming writes are bounded or coalesced so the system does not write one database row per token.
- App rendering can display a running reasoning row and continue following the bottom during same-row streaming updates.
- Tests cover Factory streaming normalization, Runtime streaming aggregation/projection, App rendering behavior, and non-streaming regression.
- The implementation avoids long-term fallback paths, ambiguous duplicate logic, and stale misleading code residue.

## Subproblems
- P001: Add LLM Factory streaming transport contract
- P002: Stream reasoning through Runtime aggregation and activity projection
- P003: Render same-row streaming reasoning updates in the App monitor
- P004: Verify and clean up reasoning streaming end to end

## Results
- R014

## Latest Check
C014

## Bodies
- Problem: problems/P000/README.md
- Ticket T000: problems/P000/tickets/T000.md
- Result R014: problems/P000/results/R014.md
- Check C014: problems/P000/checks/C014.md

## Follow-ups
- none
