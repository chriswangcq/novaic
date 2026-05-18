# P330: Attach repository payload generation audit

Status: done
Parent: P327
Root: P000
Source Ticket: T319 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P327/children/P330
Body: problems/P000/children/P004/children/P278/children/P283/children/P327/children/P330/README.md
Ticket(s): T320

## Problem
Map how `SessionRepository` decides an input is attachable, computes `expected_session_generation`, and records the attach outbox payload. Verify stale scope/session state cannot produce a misleading current-generation attach payload.

## Success Criteria
- File-reference attach decision and `expected_session_generation` computation paths.
- Classify `SessionLedgerRepository.active_generation(...)` behavior when active scope mismatches.
- Verify attach outbox payload includes scope and expected generation from authoritative state.
- Flag or fix any repository-side stale-scope attach acceptance.

## Subproblems
- none

## Results
- R315

## Latest Check
C336

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P327/children/P330/README.md
- Ticket T320: problems/P000/children/P004/children/P278/children/P283/children/P327/children/P330/tickets/T320.md
- Result R315: problems/P000/children/P004/children/P278/children/P283/children/P327/children/P330/results/R315.md
- Check C336: problems/P000/children/P004/children/P278/children/P283/children/P327/children/P330/checks/C336.md

## Follow-ups
- none
