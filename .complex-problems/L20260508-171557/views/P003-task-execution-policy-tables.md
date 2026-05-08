# P003: Task Execution Policy Tables

Status: done
Parent: P000
Root: P000
Package: problems/P000/children/P003
Body: problems/P000/children/P003/README.md
Ticket(s): T003

## Problem
Task execution still encodes idempotency, retry, completion/failure, and saga adaptation as a large imperative method. Introduce explicit decision/policy units so task behavior can be tested from input snapshots.

## Success Criteria
- Task execution has explicit policy/decision helpers or tables for idempotency and failure handling.
- Tests cover duplicate completed, in-progress contention, business error, retryable error, and success scenarios at the decision/policy boundary.
- The engine uses the plan/effect substrate from P002.
- No old direct effect branch remains.

## Subproblems
- none

## Results
- R002

## Latest Check
C002

## Bodies
- Problem: problems/P000/children/P003/README.md
- Ticket T003: problems/P000/children/P003/tickets/T003.md
- Result R002: problems/P000/children/P003/results/R002.md
- Check C002: problems/P000/children/P003/checks/C002.md

## Follow-ups
- none
