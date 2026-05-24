# P020: Add autonomous release-controller polling loop

Status: done
Parent: P019
Root: P000
Source Ticket: T019 (split)
Source Check: none
Package: problems/P000/children/P019/children/P020
Body: problems/P000/children/P019/children/P020/README.md
Ticket(s): T020

## Problem
The release-controller exposes `/v1/polls/once`, but the service does not yet own a periodic polling loop. Add a configurable background loop that invokes `BranchPoller` on service startup and shuts down cleanly.

## Success Criteria
- Config includes an explicit polling enable flag.
- When enabled, the FastAPI service starts a background task that calls `BranchPoller.poll_once()` every `poll_interval_seconds`.
- The loop can be disabled for tests or maintenance.
- Shutdown cancels the background task cleanly.
- Tests cover enabled and disabled behavior.
- Branch-triggered polling still cannot target prod.

## Subproblems
- none

## Results
- R019

## Latest Check
C021

## Bodies
- Problem: problems/P000/children/P019/children/P020/README.md
- Ticket T020: problems/P000/children/P019/children/P020/tickets/T020.md
- Result R019: problems/P000/children/P019/children/P020/results/R019.md
- Check C021: problems/P000/children/P019/children/P020/checks/C021.md

## Follow-ups
- none
