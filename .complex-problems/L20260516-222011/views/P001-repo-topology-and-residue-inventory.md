# P001: Repo topology and residue inventory

Status: done
Parent: P000
Root: P000
Source Ticket: T000 (split)
Source Check: none
Package: problems/P000/children/P001
Body: problems/P000/children/P001/README.md
Ticket(s): T001

## Problem
Audit the multi-repo workspace topology, branch/submodule status, dirty state, stale generated files, and obvious code-residue hotspots before touching implementation. This establishes the map and prevents unrelated or accidental edits.

## Success Criteria
- Current branch, submodule pointers, dirty state, and repo layout are recorded.
- Obvious residue patterns are searched with concrete commands.
- Any immediate low-risk cleanup opportunities are identified for child or follow-up work.
- No implementation edits are made without evidence and a narrower ticket.

## Subproblems
- P008: Workspace branch submodule and dirty-state inventory
- P009: Residue hotspot search and triage

## Results
- R094

## Latest Check
C108

## Bodies
- Problem: problems/P000/children/P001/README.md
- Ticket T001: problems/P000/children/P001/tickets/T001.md
- Result R094: problems/P000/children/P001/results/R094.md
- Check C108: problems/P000/children/P001/checks/C108.md

## Follow-ups
- none
