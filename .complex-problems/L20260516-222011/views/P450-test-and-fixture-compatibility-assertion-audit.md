# P450: Test and fixture compatibility assertion audit

Status: done
Parent: P405
Root: P000
Source Ticket: T440 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P405/children/P450
Body: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P405/children/P450/README.md
Ticket(s): T441

## Problem
Tests and fixtures can accidentally preserve unsafe compatibility semantics by expecting missing/stale generation or legacy active-state behavior to succeed.

## Success Criteria
- Inventory compatibility/generation/legacy hits in tests and fixtures.
- Inspect suspicious assertions around missing/stale generation, fallback, legacy, and active-session behavior.
- Rewrite/delete unsafe assertions if found.
- Classify retained test hits as negative guards or harmless fixtures.

## Subproblems
- none

## Results
- R435

## Latest Check
C461

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P405/children/P450/README.md
- Ticket T441: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P405/children/P450/tickets/T441.md
- Result R435: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P405/children/P450/results/R435.md
- Check C461: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P405/children/P450/checks/C461.md

## Follow-ups
- none
