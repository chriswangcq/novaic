# P026: Phase 3.4: Cut tool step recording to events

Status: done
Parent: P004
Root: P000
Package: problems/P000/children/P004/children/P026
Body: problems/P000/children/P004/children/P026/README.md
Ticket(s): T030

## Problem
Tool call/result observations are currently persisted as legacy `steps/*.json`, `steps/_index.jsonl`, and payload records. The authoritative fact must become `ToolStepRecorded` ContextEvents, with payload bytes still stored through the explicit payload/blob path when needed.

## Success Criteria
- `/v1/steps/write` appends `ToolStepRecorded` events.
- Event payloads preserve call id, tool name, status, observation preview/summary/head, payload ref, and scope id.
- Legacy step files, if still created, are projection/debug artifacts only.
- Tests verify event stream content and no hidden payload file read is required for projection.

## Subproblems
- P035: Phase 3.4.1: Normalize tool step payloads before event emission
- P036: Phase 3.4.2: Wire steps/write to ToolStepRecorded events
- P037: Phase 3.4.3: Verify tool step cutover boundaries

## Results
- R031

## Latest Check
C033

## Bodies
- Problem: problems/P000/children/P004/children/P026/README.md
- Ticket T030: problems/P000/children/P004/children/P026/tickets/T030.md
- Result R031: problems/P000/children/P004/children/P026/results/R031.md
- Check C033: problems/P000/children/P004/children/P026/checks/C033.md

## Follow-ups
- none
