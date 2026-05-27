# P013: Review streaming contracts and remove misleading residue

Status: done
Parent: P004
Root: P000
Source Ticket: T011 (split)
Source Check: none
Package: problems/P000/children/P004/children/P013
Body: problems/P000/children/P004/children/P013/README.md
Ticket(s): T013

## Problem
The code should express one clean long-term path: Factory streaming chunks, Runtime aggregation/projection, Entangled activity records, and App Timeline rendering. The diff/source must not leave long-lived fallback branches, stale misleading paths, or raw partial reasoning accidentally added into future LLM input history.

## Success Criteria
- Source review finds no long-term fallback branch for the new reasoning streaming path.
- Runtime aggregation returns a final assistant response while activity projection uses streaming deltas without injecting partial reasoning into the next LLM input history.
- App path review confirms no parallel reasoning transport and no stale monitor path left by this work.
- Any cleanup needed is implemented and covered by focused tests or explicit evidence.

## Subproblems
- none

## Results
- R011

## Latest Check
C011

## Bodies
- Problem: problems/P000/children/P004/children/P013/README.md
- Ticket T013: problems/P000/children/P004/children/P013/tickets/T013.md
- Result R011: problems/P000/children/P004/children/P013/results/R011.md
- Check C011: problems/P000/children/P004/children/P013/checks/C011.md

## Follow-ups
- none
