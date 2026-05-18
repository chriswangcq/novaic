# P232: Audit Cortex event projection preserves payload pointers

Status: done
Parent: P229
Root: P000
Source Ticket: T222 (split)
Source Check: none
Package: problems/P000/children/P003/children/P129/children/P229/children/P232
Body: problems/P000/children/P003/children/P129/children/P229/children/P232/README.md
Ticket(s): T228

## Problem
Cortex event streams and projections must preserve compact pointer metadata (`step_ref`, `payload_ref`, artifacts/projection summaries) without expanding durable payload bodies into normal event/context records.

This belongs under `P229` because event projection is the middle layer between durable write storage and runtime context preparation.

## Success Criteria
- Event writer/projection paths are mapped with file/function pointers.
- Projection behavior is shown to preserve refs and compact summaries rather than full payload bytes/text.
- Focused event projection tests pass or are added if coverage is missing.

## Subproblems
- none

## Results
- R224

## Latest Check
C238

## Bodies
- Problem: problems/P000/children/P003/children/P129/children/P229/children/P232/README.md
- Ticket T228: problems/P000/children/P003/children/P129/children/P229/children/P232/tickets/T228.md
- Result R224: problems/P000/children/P003/children/P129/children/P229/children/P232/results/R224.md
- Check C238: problems/P000/children/P003/children/P129/children/P229/children/P232/checks/C238.md

## Follow-ups
- none
