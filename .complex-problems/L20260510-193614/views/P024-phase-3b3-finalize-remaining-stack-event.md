# P024: Phase 3B3 Finalize Remaining Stack Event

Status: done
Parent: P018
Root: P000
Package: problems/P000/children/P004/children/P018/children/P024
Body: problems/P000/children/P004/children/P018/children/P024/README.md
Ticket(s): T020

## Problem
Root finalize/scope archive currently writes a wake archived context event with `remaining_stack=[]`. Phase 3 needs explicit durable finalize semantics that records reason and actual remaining operational stack before clearing/updating projection.

## Success Criteria
- Finalize/root archive records explicit reason and remaining stack into operational SQLite event/projection state.
- Active-stack projection is cleared or updated deterministically after finalize.
- Idempotent finalize/retry behavior does not duplicate conflicting stack events.
- Tests cover root archive with empty and non-empty child stack cases.

## Subproblems
- P027: Phase 3B3A Active Stack Finalize Helper
- P028: Phase 3B3B Scope Archive Finalize Wiring
- P029: Phase 3B3C Finalize Verification And Residue Check

## Results
- R020

## Latest Check
C022

## Bodies
- Problem: problems/P000/children/P004/children/P018/children/P024/README.md
- Ticket T020: problems/P000/children/P004/children/P018/children/P024/tickets/T020.md
- Result R020: problems/P000/children/P004/children/P018/children/P024/results/R020.md
- Check C022: problems/P000/children/P004/children/P018/children/P024/checks/C022.md

## Follow-ups
- none
