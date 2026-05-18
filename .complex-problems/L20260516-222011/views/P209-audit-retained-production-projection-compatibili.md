# P209: Audit retained production projection compatibility branches

Status: done
Parent: P199
Root: P000
Source Ticket: T195 (split)
Source Check: none
Package: problems/P000/children/P003/children/P127/children/P187/children/P199/children/P209
Body: problems/P000/children/P003/children/P127/children/P187/children/P199/children/P209/README.md
Ticket(s): T198

## Problem
Not every old-looking projection branch is stale. Nested result unwrapping, generic dict fallback, and historical step parsing may still defend persisted data. Audit retained production branches and either justify or remove them with evidence.

## Success Criteria
- Each retained compatibility/defensive branch has a concrete reason tied to current or persisted data contracts.
- Any branch found stale is removed in the child work, not merely documented.
- Tests cover the retained behavior or confirm the stale branch is gone.

## Subproblems
- P210: Audit nested result wrapper projection branch
- P211: Audit MCP image/data-url projection branch
- P212: Audit generic dict JSON fallback projection branch

## Results
- R196

## Latest Check
C210

## Bodies
- Problem: problems/P000/children/P003/children/P127/children/P187/children/P199/children/P209/README.md
- Ticket T198: problems/P000/children/P003/children/P127/children/P187/children/P199/children/P209/tickets/T198.md
- Result R196: problems/P000/children/P003/children/P127/children/P187/children/P199/children/P209/results/R196.md
- Check C210: problems/P000/children/P003/children/P127/children/P187/children/P199/children/P209/checks/C210.md

## Follow-ups
- none
