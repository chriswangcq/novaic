# P354: Subagent finalize status identity guard

Status: done
Parent: P350
Root: P000
Source Ticket: T339 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P350/children/P354
Body: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P350/children/P354/README.md
Ticket(s): T341

## Problem
`task_queue/handlers/subagent_handlers.py::handle_subagent_set_sleeping` and `handle_subagent_set_completed` mutate Business subagent status from finalize-related tasks using only coarse agent/subagent identity. A stale finalize task may incorrectly move a currently active subagent to sleeping/completed unless the handler checks wake/session identity or the mutation is proven harmless.

This child belongs under P350 because Business status mutation was identified as a live stale-finalize risk in P348.

## Success Criteria
- Inspect subagent status payload builders in `wake_finalize` and the Business handlers that mutate status.
- Add explicit expected wake/session identity checks before status mutation, or document why the status transition is structurally independent from wake finalization.
- Add tests for missing identity and stale identity.
- Remove any compatibility path that lets missing identity mutate status.

## Subproblems
- P357: Subagent finalize status payload identity
- P358: Subagent finalize status handler validation
- P359: Wake finalize status gating order
- P360: Subagent finalize status identity aggregate verification

## Results
- R338

## Latest Check
C359

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P350/children/P354/README.md
- Ticket T341: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P350/children/P354/tickets/T341.md
- Result R338: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P350/children/P354/results/R338.md
- Check C359: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P350/children/P354/checks/C359.md

## Follow-ups
- none
