# P653: Audit Live Code for Blob-as-Workspace Authority

Status: done
Parent: P649
Root: P000
Source Ticket: T648 (split)
Source Check: none
Package: problems/P000/children/P005/children/P554/children/P632/children/P649/children/P653
Body: problems/P000/children/P005/children/P554/children/P632/children/P649/children/P653/README.md
Ticket(s): T649

## Problem
Live code may still let Blob APIs act as the authority for Cortex workspace semantics, bypassing Workspace/LogicalFS boundaries. This child should inspect runtime code paths, not broad docs.

## Success Criteria
- Scan live code under `novaic-cortex`, `novaic-agent-runtime`, `novaic-logicalfs`, `novaic-sandbox-service`, `novaic-sandbox-sdk`, and `novaic-common` for Blob/workspace authority patterns.
- Classify live matches as valid artifact/file service, durable byte store behind Workspace, or active semantic bypass.
- Remove or spawn a concrete follow-up for any active semantic bypass.

## Subproblems
- none

## Results
- R644

## Latest Check
C686

## Bodies
- Problem: problems/P000/children/P005/children/P554/children/P632/children/P649/children/P653/README.md
- Ticket T649: problems/P000/children/P005/children/P554/children/P632/children/P649/children/P653/tickets/T649.md
- Result R644: problems/P000/children/P005/children/P554/children/P632/children/P649/children/P653/results/R644.md
- Check C686: problems/P000/children/P005/children/P554/children/P632/children/P649/children/P653/checks/C686.md

## Follow-ups
- none
