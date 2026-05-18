# P350: Cortex finalize mutation identity guards

Status: done
Parent: P337
Root: P000
Source Ticket: T336 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P350
Body: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P350/README.md
Ticket(s): T339

## Problem
Cortex-facing finalize or scope-end handlers must not close or archive a newer wake/skill stack from a stale finalize task. Identify and enforce expected wake scope/session generation checks before Cortex mutation where the handler mutates state.

## Success Criteria
- Inspect `task_queue/handlers/cortex_handlers.py`, related bridge code, and tests.
- Verify scope/generation identity is checked before `scope_end`, stack archive, input append, or message acknowledgement.
- Add tests for missing/stale scope and generation if a mutating path lacks coverage.
- If Cortex mutation is structurally keyed by scope path rather than session generation, document why that is safe or add the missing check.

## Subproblems
- P353: Cortex scope_end identity contract
- P354: Subagent finalize status identity guard
- P355: Wake finalize mutation payload propagation
- P356: Finalize mutation guard aggregate verification

## Results
- R341

## Latest Check
C362

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P350/README.md
- Ticket T339: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P350/tickets/T339.md
- Result R341: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P350/results/R341.md
- Check C362: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P350/checks/C362.md

## Follow-ups
- none
