# P382: Runtime finalize source guard classification

Status: done
Parent: P378
Root: P000
Source Ticket: T369 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P378/children/P382
Body: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P378/children/P382/README.md
Ticket(s): T371

## Problem
Runtime source must be scanned for stale finalize/session-ended compatibility residue that tests might not exercise: unsafe generation coercion, missing generation defaults, direct active clears, and current-active fallback behavior.

## Success Criteria
- Runtime source guards are run over `queue_service`, `task_queue`, and relevant tests.
- Every guard hit is classified as safe, fixed, or moved into a follow-up problem.
- No live runtime path remains that can clear, restart, or archive a newer active session from stale/missing generation.
- The result includes file-level evidence for the classification.

## Subproblems
- none

## Results
- R364

## Latest Check
C387

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P378/children/P382/README.md
- Ticket T371: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P378/children/P382/tickets/T371.md
- Result R364: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P378/children/P382/results/R364.md
- Check C387: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P378/children/P382/checks/C387.md

## Follow-ups
- none
