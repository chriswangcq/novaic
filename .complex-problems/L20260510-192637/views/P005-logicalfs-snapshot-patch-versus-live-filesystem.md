# P005: LogicalFS Snapshot Patch Versus Live Filesystem

Status: done
Parent: P000
Root: P000
Package: problems/P000/children/P005
Body: problems/P000/children/P005/README.md
Ticket(s): T005

## Problem
Shell uses a materialized LogicalFS snapshot and writes RW changes back on release. This is clean enough for current shell execution, but not a fully live realtime LogicalFS service.

## Success Criteria
- Decide whether snapshot/patch is the final model or a phase before live LogicalFS.
- If live LogicalFS is desired, define how SQLite/LogicalFS metadata and Blob bytes participate.
- Include correctness rules for crash recovery, concurrent subagents, and no explicit commit.

## Subproblems
- none

## Results
- R004

## Latest Check
C004

## Bodies
- Problem: problems/P000/children/P005/README.md
- Ticket T005: problems/P000/children/P005/tickets/T005.md
- Result R004: problems/P000/children/P005/results/R004.md
- Check C004: problems/P000/children/P005/checks/C004.md

## Follow-ups
- none
