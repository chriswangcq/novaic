# P011: Release-controller core unit tests

Status: done
Parent: P002
Root: P000
Source Ticket: T002 (split)
Source Check: none
Package: problems/P000/children/P002/children/P011
Body: problems/P000/children/P002/children/P011/README.md
Ticket(s): T007

## Problem
Add focused unit tests for the release-controller core so the first implementation has executable proof for the rules that matter most.

This belongs under P002 because core behavior must be testable before Docker packaging, CI guard wiring, and host deployment build on top of it.

## Success Criteria
- Tests cover branch mapping for main, release, and preview branch rules.
- Tests cover immutable image ref acceptance and rejection.
- Tests cover state persistence across store reload.
- Tests cover current and previous pointer updates on successful namespace release.
- Tests cover dry-run command planning without executing host Docker or deploy commands.
- Tests cover API endpoint behavior when the local dependency set supports in-process API testing.

## Subproblems
- none

## Results
- R005

## Latest Check
C005

## Bodies
- Problem: problems/P000/children/P002/children/P011/README.md
- Ticket T007: problems/P000/children/P002/children/P011/tickets/T007.md
- Result R005: problems/P000/children/P002/children/P011/results/R005.md
- Check C005: problems/P000/children/P002/children/P011/checks/C005.md

## Follow-ups
- none
