# P008: Release-controller persistent state store

Status: done
Parent: P002
Root: P000
Source Ticket: T002 (split)
Source Check: none
Package: problems/P000/children/P002/children/P008
Body: problems/P000/children/P002/children/P008/README.md
Ticket(s): T004

## Problem
Implement durable state persistence for branch heads, release runs, current and previous release pointers, candidates, and failures using atomic JSON writes under a configured state directory.

This belongs under P002 because the controller must be restart-safe before it can safely build, deploy, promote, or roll back releases.

## Success Criteria
- State store initializes the required directory structure without relying on hidden global paths.
- Branch heads can be read and written by branch name.
- Release run records can be created, updated through lifecycle states, listed, and fetched by id.
- Current and previous pointers are updated atomically when a namespace release succeeds.
- Candidate release pointers can be recorded separately from deployed namespace pointers.
- Failure details are persisted on failed runs and survive process restart.

## Subproblems
- none

## Results
- R002

## Latest Check
C002

## Bodies
- Problem: problems/P000/children/P002/children/P008/README.md
- Ticket T004: problems/P000/children/P002/children/P008/tickets/T004.md
- Result R002: problems/P000/children/P002/children/P008/results/R002.md
- Check C002: problems/P000/children/P002/children/P008/checks/C002.md

## Follow-ups
- none
