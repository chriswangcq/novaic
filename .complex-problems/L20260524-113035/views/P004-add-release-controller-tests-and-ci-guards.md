# P004: Add release-controller tests and CI guards

Status: done
Parent: P000
Root: P000
Source Ticket: T000 (split)
Source Check: none
Package: problems/P000/children/P004
Body: problems/P000/children/P004/README.md
Ticket(s): T013

## Problem
The new release-controller path must be protected against ambiguous branch rules, mutable image tags, unsafe prod auto-deploy, missing dry-run, and stale GitHub-Actions-primary documentation.

## Success Criteria
- Tests and guards run locally without external services.
- Guard rejects prod auto-deploy from ordinary branch polling.
- Guard requires immutable refs/digests for prod promotion.
- Guard verifies controller docs are primary and GitHub Actions is secondary.
- Existing relevant tests/guards still pass.

## Subproblems
- none

## Results
- R012

## Latest Check
C013

## Bodies
- Problem: problems/P000/children/P004/README.md
- Ticket T013: problems/P000/children/P004/tickets/T013.md
- Result R012: problems/P000/children/P004/results/R012.md
- Check C013: problems/P000/children/P004/checks/C013.md

## Follow-ups
- none
