# P439: Context endpoint ownership and migration

Status: done
Parent: P436
Root: P000
Source Ticket: T425 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P419/children/P436/children/P439
Body: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P419/children/P436/children/P439/README.md
Ticket(s): T429

## Problem
The context projection endpoints may still be useful, but only with explicit ownership. `/v1/context/read`, `/v1/context/append`, and `/v1/context/batch` must either be current intentional APIs or removed/migrated from runtime paths.

## Success Criteria
- Each context endpoint has an explicit owner and purpose: notification injection, debug API, tests, or removed legacy.
- Runtime bridge helpers are renamed, narrowed, or deleted if their names imply stale LLM history ownership.
- Live runtime code does not use compatibility context projection as the authoritative LLM context source.
- Focused runtime/Cortex tests pass after any cleanup.

## Subproblems
- P442: Materialized context owner classification
- P443: Runtime bridge materialized context helper narrowing
- P444: Context task handler projection contract cleanup
- P445: Cortex context endpoint and test cleanup

## Results
- R425

## Latest Check
C451

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P419/children/P436/children/P439/README.md
- Ticket T429: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P419/children/P436/children/P439/tickets/T429.md
- Result R425: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P419/children/P436/children/P439/results/R425.md
- Check C451: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P419/children/P436/children/P439/checks/C451.md

## Follow-ups
- none
