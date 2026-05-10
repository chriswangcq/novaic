# P044: Phase 3.6.3: Add write-path event authority tests

Status: done
Parent: P028
Root: P000
Package: problems/P000/children/P004/children/P028/children/P044
Body: problems/P000/children/P004/children/P028/children/P044/README.md
Ticket(s): T050

## Problem
Individual endpoint tests verify event rows, but Phase 3 needs a consolidated authority test that proves root/wake, notifications, context append/batch, tool steps, and skill begin/end all leave ContextEvents as the write artifact.

## Success Criteria
- A focused test exercises the Phase 3 write path set and reads `context_events/events.jsonl`.
- The test asserts expected event types and key payload fields.
- The test does not rely on legacy `context.jsonl`, `steps/*.json`, or `summary.md` as authoritative evidence.
- Full Cortex suite passes.

## Subproblems
- none

## Results
- R047

## Latest Check
C050

## Bodies
- Problem: problems/P000/children/P004/children/P028/children/P044/README.md
- Ticket T050: problems/P000/children/P004/children/P028/children/P044/tickets/T050.md
- Result R047: problems/P000/children/P004/children/P028/children/P044/results/R047.md
- Check C050: problems/P000/children/P004/children/P028/children/P044/checks/C050.md

## Follow-ups
- none
