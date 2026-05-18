# P180: Active stack source and projection map

Status: done
Parent: P137
Root: P000
Source Ticket: T169 (split)
Source Check: none
Package: problems/P000/children/P003/children/P126/children/P137/children/P180
Body: problems/P000/children/P003/children/P126/children/P137/children/P180/README.md
Ticket(s): T170

## Problem
Active skill stack state is produced by Cortex lifecycle APIs and stored/projected through operational state. Before judging final LLM ordering, the source of truth must be mapped: where frames are written, read, finalized, and how stale file-walk or duplicate stack sources are avoided.

## Success Criteria
- Identify the active stack source of truth and all production write/read/finalize call sites.
- Document whether active stack state is SQLite/operational-store backed or file-walk backed.
- Run focused Cortex tests covering active stack projection, lifecycle APIs, and source guardrails.
- Fix or split any stale source path that can bypass the active stack projection.

## Subproblems
- none

## Results
- R166

## Latest Check
C180

## Bodies
- Problem: problems/P000/children/P003/children/P126/children/P137/children/P180/README.md
- Ticket T170: problems/P000/children/P003/children/P126/children/P137/children/P180/tickets/T170.md
- Result R166: problems/P000/children/P003/children/P126/children/P137/children/P180/results/R166.md
- Check C180: problems/P000/children/P003/children/P126/children/P137/children/P180/checks/C180.md

## Follow-ups
- none
