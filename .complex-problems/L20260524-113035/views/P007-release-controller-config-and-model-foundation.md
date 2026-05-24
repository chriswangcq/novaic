# P007: Release-controller config and model foundation

Status: done
Parent: P002
Root: P000
Source Ticket: T002 (split)
Source Check: none
Package: problems/P000/children/P002/children/P007
Body: problems/P000/children/P002/children/P007/README.md
Ticket(s): T003

## Problem
Create the release-controller package foundation with explicit configuration loading and typed domain models for branch rules, run states, image refs, namespaces, and command plans.

This belongs under P002 because every later core service slice depends on the same validated configuration and shared model vocabulary.

## Success Criteria
- A clear release-controller package exists in the repository.
- Config loading supports repo path or URL, branch rules, registry image names, deploy script path, poll interval, dry-run default, state directory, and server bind settings.
- Branch rule models preserve stable service names and isolate environments through namespace.
- Run state and command plan models are explicit enough for state persistence, planner, and API modules to share.
- Invalid configuration fails loudly with a useful error instead of falling back to implicit defaults.

## Subproblems
- none

## Results
- R001

## Latest Check
C001

## Bodies
- Problem: problems/P000/children/P002/children/P007/README.md
- Ticket T003: problems/P000/children/P002/children/P007/tickets/T003.md
- Result R001: problems/P000/children/P002/children/P007/results/R001.md
- Check C001: problems/P000/children/P002/children/P007/checks/C001.md

## Follow-ups
- none
