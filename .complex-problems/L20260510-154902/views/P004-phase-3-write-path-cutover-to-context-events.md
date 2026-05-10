# P004: Phase 3: Write-path cutover to context events

Status: done
Parent: P000
Root: P000
Package: problems/P000/children/P004
Body: problems/P000/children/P004/README.md
Ticket(s): T020

## Problem
Cut Cortex write paths over so context facts are appended as events first. Legacy files may still be generated as projections if needed, but direct file writes must no longer be the source-of-truth path.

## Success Criteria
- `context.append`, `context.batch`, `steps.write`, `skill_begin`, `skill_end`, wake init, and notification input append emit context events as the authoritative fact.
- Workspace projection files, if still present, are explicitly derived/projection-only.
- Old direct-source writes are deleted or routed through event append/projector.
- Tests cover each write endpoint and verify event stream contents.

## Subproblems
- P023: Phase 3.1: Map write paths and introduce explicit ContextEvent writer
- P024: Phase 3.2: Cut root/wake initialization and notifications to events
- P025: Phase 3.3: Cut context append and batch writes to events
- P026: Phase 3.4: Cut tool step recording to events
- P027: Phase 3.5: Cut skill begin/end lifecycle to events
- P028: Phase 3.6: Demote or delete legacy source writes and verify write cutover

## Results
- R050

## Latest Check
C053

## Bodies
- Problem: problems/P000/children/P004/README.md
- Ticket T020: problems/P000/children/P004/tickets/T020.md
- Result R050: problems/P000/children/P004/results/R050.md
- Check C053: problems/P000/children/P004/checks/C053.md

## Follow-ups
- none
