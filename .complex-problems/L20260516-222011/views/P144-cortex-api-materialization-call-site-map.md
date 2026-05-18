# P144: Cortex API materialization call-site map

Status: done
Parent: P134
Root: P000
Source Ticket: T127 (split)
Source Check: none
Package: problems/P000/children/P003/children/P126/children/P134/children/P144
Body: problems/P000/children/P003/children/P126/children/P134/children/P144/README.md
Ticket(s): T145

## Problem
Cortex API endpoints may append ContextEvents and also materialize debug projections into workspace files. These call sites must be mapped so event authority and projection materialization remain intentionally paired.

## Success Criteria
- API call sites for context message writes, batch writes, tool step writes, and payload reads are mapped with source pointers.
- Each call site is classified as authoritative event append, materialized projection write, explicit payload retrieval, or legacy/stale path.
- Tests covering API context writes and step writes are identified and run.
- Any duplicate active write path that can diverge from ContextEvents is fixed or split.

## Subproblems
- none

## Results
- R141

## Latest Check
C155

## Bodies
- Problem: problems/P000/children/P003/children/P126/children/P134/children/P144/README.md
- Ticket T145: problems/P000/children/P003/children/P126/children/P134/children/P144/tickets/T145.md
- Result R141: problems/P000/children/P003/children/P126/children/P134/children/P144/results/R141.md
- Check C155: problems/P000/children/P003/children/P126/children/P134/children/P144/checks/C155.md

## Follow-ups
- none
