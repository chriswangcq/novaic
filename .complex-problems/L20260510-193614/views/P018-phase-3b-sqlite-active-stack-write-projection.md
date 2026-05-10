# P018: Phase 3B SQLite Active Stack Write Projection

Status: done
Parent: P004
Root: P000
Package: problems/P000/children/P004/children/P018
Body: problems/P000/children/P004/children/P018/README.md
Ticket(s): T016

## Problem
`skill_begin`, `skill_end`, and finalize need to update operational SQLite active-stack projection transactionally with their lifecycle events. Without this write path, runtime reads cannot safely cut over from file walking.

## Success Criteria
- A small adapter/helper writes active-stack frames to `OperationalSqliteStore.set_active_stack` with explicit root id, top scope id, generation, and frame schema.
- `skill_begin` updates SQLite active-stack projection after a successful child scope open.
- `skill_end` updates SQLite active-stack projection after a successful close.
- Finalize records explicit reason and remaining stack in a durable event/projection update.
- Tests cover nested begin/end and projection state after restart-like store reuse.

## Subproblems
- P022: Phase 3B1 Active Stack Projection Helper
- P023: Phase 3B2 Skill Begin End Stack Writes
- P024: Phase 3B3 Finalize Remaining Stack Event
- P025: Phase 3B4 Stack Write Projection Verification

## Results
- R022

## Latest Check
C024

## Bodies
- Problem: problems/P000/children/P004/children/P018/README.md
- Ticket T016: problems/P000/children/P004/children/P018/tickets/T016.md
- Result R022: problems/P000/children/P004/children/P018/results/R022.md
- Check C024: problems/P000/children/P004/children/P018/checks/C024.md

## Follow-ups
- none
