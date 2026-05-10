# P014: Clean Stale Blob Language In Architecture Docs

Status: done
Parent: P008
Root: P000
Package: problems/P000/children/P004/children/P008/children/P014
Body: problems/P000/children/P004/children/P008/children/P014/README.md
Ticket(s): T012

## Problem
Architecture and reference docs still contain broad "Blob-backed Workspace" or "Cortex uses Blob Service object APIs for production backend" phrasing. These docs should distinguish Blob as cheap byte/object persistence from LogicalFS/Cortex file authority for live `RO` / `RW`.

This child belongs under T010 because docs require a separate semantic pass from code comments.

## Success Criteria
- `docs/architecture/*`, `docs/cortex/*`, and `docs/reference/blob-service.md` no longer claim Blob is the live `RO` / `RW` authority.
- Transitional object API references are marked as adapter/internal or historical, not the desired live file path.
- Blob usage for artifacts/display/download remains described as cheap byte serving.

## Subproblems
- none

## Results
- R009

## Latest Check
C009

## Bodies
- Problem: problems/P000/children/P004/children/P008/children/P014/README.md
- Ticket T012: problems/P000/children/P004/children/P008/children/P014/tickets/T012.md
- Result R009: problems/P000/children/P004/children/P008/children/P014/results/R009.md
- Check C009: problems/P000/children/P004/children/P008/children/P014/checks/C009.md

## Follow-ups
- none
