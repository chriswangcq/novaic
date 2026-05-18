# P481: Direct side-effect bypass cleanup

Status: done
Parent: P279
Root: P000
Source Ticket: T474 (split)
Source Check: none
Package: problems/P000/children/P004/children/P279/children/P481
Body: problems/P000/children/P004/children/P279/children/P481/README.md
Ticket(s): T476

## Problem
Some queue/session/runtime paths may still create sagas, publish queue messages, or perform external side effects directly instead of routing through explicit FSM/outbox boundaries. P279 needs the direct side-effect surface classified and any high-confidence stale bypass removed or tightened.

## Success Criteria
- Direct `SagaOrchestrator.create`, `queue.publish`, and session side-effect call sites in the audited runtime/session paths are classified.
- Required adapter/outbox dispatcher boundaries are documented and retained.
- High-confidence stale bypasses are removed or replaced with explicit FSM/outbox effects.
- Ambiguous side-effect call sites are split into smaller follow-up problems.
- Focused side-effect/outbox tests pass after any source change.

## Subproblems
- P484: Production side-effect callsite classification
- P485: Generic task publish route boundary decision
- P486: Session outbox dispatcher boundary hardening
- P487: Direct side-effect bypass final verification

## Results
- R477

## Latest Check
C506

## Bodies
- Problem: problems/P000/children/P004/children/P279/children/P481/README.md
- Ticket T476: problems/P000/children/P004/children/P279/children/P481/tickets/T476.md
- Result R477: problems/P000/children/P004/children/P279/children/P481/results/R477.md
- Check C506: problems/P000/children/P004/children/P279/children/P481/checks/C506.md

## Follow-ups
- none
