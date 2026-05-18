# P279: Legacy imperative dispatch and compatibility residue cleanup

Status: done
Parent: P004
Root: P000
Source Ticket: T273 (split)
Source Check: none
Package: problems/P000/children/P004/children/P279
Body: problems/P000/children/P004/children/P279/README.md
Ticket(s): T474

## Problem
Search for old imperative dispatch/finalize/session branches that bypass or duplicate the FSM decision path, and remove or tighten high-confidence stale residue.

## Success Criteria
- Static scan for direct SagaOrchestrator/session mutation/finalize compatibility branches is recorded.
- High-confidence stale code is removed or replaced with explicit FSM/outbox path.
- If ambiguous, create a smaller follow-up problem instead of speculative deletion.

## Subproblems
- P480: Imperative dispatch residue inventory
- P481: Direct side-effect bypass cleanup
- P482: Finalize and session compatibility branch cleanup
- P483: Imperative dispatch cleanup final verification

## Results
- R499

## Latest Check
C528

## Bodies
- Problem: problems/P000/children/P004/children/P279/README.md
- Ticket T474: problems/P000/children/P004/children/P279/tickets/T474.md
- Result R499: problems/P000/children/P004/children/P279/results/R499.md
- Check C528: problems/P000/children/P004/children/P279/checks/C528.md

## Follow-ups
- none
