# P009: Release-controller branch planner and command runner

Status: done
Parent: P002
Root: P000
Source Ticket: T002 (split)
Source Check: none
Package: problems/P000/children/P002/children/P009
Body: problems/P000/children/P002/children/P009/README.md
Ticket(s): T005

## Problem
Implement the core planning logic that maps branch changes and manual requests to deterministic release actions, validates immutable refs, and turns actions into verification/build/publish/deploy command plans that can run in dry-run or real execution mode.

This belongs under P002 because this is the controller's release brain: API and polling should call into this module instead of duplicating deployment rules.

## Success Criteria
- Branch rules map `main` to staging auto-deploy, `preview/*` to preview namespace auto-deploy, and `release/*` to candidate-only behavior.
- Branch polling or branch-triggered runs cannot deploy prod.
- Prod promotion accepts only digest refs or sha tags and rejects `latest` or mutable semantic tags.
- Rollback planning uses recorded previous pointers and validates immutable image refs.
- Dry-run planning emits explicit command steps without executing host commands.
- Real execution goes through an injectable command runner that records stdout, stderr, exit code, and failures.

## Subproblems
- none

## Results
- R003

## Latest Check
C003

## Bodies
- Problem: problems/P000/children/P002/children/P009/README.md
- Ticket T005: problems/P000/children/P002/children/P009/tickets/T005.md
- Result R003: problems/P000/children/P002/children/P009/results/R003.md
- Check C003: problems/P000/children/P002/children/P009/checks/C003.md

## Follow-ups
- none
