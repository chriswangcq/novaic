# P059: Old data reset and no-compat behavior

Status: done
Parent: P006
Root: P000
Package: problems/P000/children/P006/children/P059
Body: problems/P000/children/P006/children/P059/README.md
Ticket(s): T059

## Problem
Define and implement explicit no-compat behavior for legacy-only roots or missing ContextEvent logs. Old data may be deleted/reset; the system must not silently fall back to legacy DFS files.

## Success Criteria
- Missing/empty event logs in active prepare/status paths have explicit behavior.
- Legacy-only materialized roots do not silently produce LLM context through DFS.
- Tests cover reset/no-compat behavior.

## Subproblems
- none

## Results
- R057

## Latest Check
C060

## Bodies
- Problem: problems/P000/children/P006/children/P059/README.md
- Ticket T059: problems/P000/children/P006/children/P059/tickets/T059.md
- Result R057: problems/P000/children/P006/children/P059/results/R057.md
- Check C060: problems/P000/children/P006/children/P059/checks/C060.md

## Follow-ups
- none
