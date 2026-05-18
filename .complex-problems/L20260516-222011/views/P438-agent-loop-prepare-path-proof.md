# P438: Agent loop prepare-path proof

Status: done
Parent: P436
Root: P000
Source Ticket: T425 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P419/children/P436/children/P438
Body: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P419/children/P436/children/P438/README.md
Ticket(s): T428

## Problem
The current LLM request assembly path must be proven to use the authoritative event/source snapshot path rather than stale materialized context projection endpoints.

## Success Criteria
- The live agent loop path from inbound message/session to LLM request creation is traced with source slices.
- The role of `prepare_for_llm`, context event snapshots, active skill stack injection, and tool observation projection is documented.
- Tests or guards prove the LLM prepare path does not call `/v1/context/read` as its source of history.
- Any stale live path discovered is fixed or split.

## Subproblems
- none

## Results
- R420

## Latest Check
C446

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P419/children/P436/children/P438/README.md
- Ticket T428: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P419/children/P436/children/P438/tickets/T428.md
- Result R420: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P419/children/P436/children/P438/results/R420.md
- Check C446: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P419/children/P436/children/P438/checks/C446.md

## Follow-ups
- none
