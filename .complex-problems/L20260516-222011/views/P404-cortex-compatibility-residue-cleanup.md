# P404: Cortex compatibility residue cleanup

Status: done
Parent: P329
Root: P000
Source Ticket: T393 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404
Body: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/README.md
Ticket(s): T405

## Problem
Cortex context/operational/archive paths may still contain compatibility residue around generation defaults, active-state lookup, archive diagnostics, or context event lifecycle. Any live Cortex residue found by the inventory must be removed and tested.

## Success Criteria
- Inspect all Cortex hits from the inventory matrix.
- Remove dangerous Cortex compatibility branches or replace them with explicit validators.
- Preserve legitimate diagnostic/projection/counter behavior only with explicit classification.
- Add focused Cortex tests for every changed live boundary.
- Rerun Cortex-focused tests and Cortex guard searches until no unclassified Cortex residue remains.

## Subproblems
- P416: Cortex residue inventory and live-surface map
- P417: Cortex context event lifecycle cleanup
- P418: Cortex archive and diagnostic residue cleanup
- P419: Cortex API CLI and bridge surface cleanup
- P420: Cortex compatibility final verification

## Results
- R434

## Latest Check
C460

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/README.md
- Ticket T405: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/tickets/T405.md
- Result R434: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/results/R434.md
- Check C460: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/checks/C460.md

## Follow-ups
- none
