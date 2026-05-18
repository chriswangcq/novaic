# P361: Recovery compensation finalize source map

Status: done
Parent: P351
Root: P000
Source Ticket: T348 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P351/children/P361
Body: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P351/children/P361/README.md
Ticket(s): T349

## Problem
Before changing recovery behavior, identify every recovery or compensation path that can synthesize `wake_finalize` or equivalent finalize mutation work. This belongs under P351 because identity hardening cannot be complete if a hidden source path still creates ambiguous finalize tasks.

## Success Criteria
- Inspect `queue_service/saga_repo.py`, `queue_service/session_recovery.py`, saga compensation code, and related tests.
- Produce a concise source map of every path that creates or replays `wake_finalize` after failure/recovery.
- Identify the source of `scope_id`, wake/root scope path, subagent id, and session generation for each path.
- Mark any ambiguous path as requiring a downstream child fix rather than treating it as safe.

## Subproblems
- none

## Results
- R342

## Latest Check
C363

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P351/children/P361/README.md
- Ticket T349: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P351/children/P361/tickets/T349.md
- Result R342: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P351/children/P361/results/R342.md
- Check C363: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P351/children/P361/checks/C363.md

## Follow-ups
- none
