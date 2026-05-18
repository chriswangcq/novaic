# P378: Runtime finalize generation aggregate regression

Status: done
Parent: P339
Root: P000
Source Ticket: T368 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P378
Body: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P378/README.md
Ticket(s): T369

## Problem
Runtime finalize/session-ended behavior needs a focused aggregate regression pass after targeted fixes. The pass must prove repository, FSM, outbox, handler, recovery, watchdog, restart, and pending-input paths reject stale or missing generation and cannot mutate a newer active session.

## Success Criteria
- Focused runtime pytest suites covering finalize ownership, session FSM, outbox cutover, recovery/watchdog, restart/pending input, attach/finalize generation checks, and legacy cleanup pass.
- Runtime source guards for missing generation, bool generation coercion, direct active clearing, and fallback generation behavior are run and classified.
- Any unsafe runtime hit is fixed or converted into a follow-up problem.
- The result records exact commands, pass/fail counts, and residual risks.

## Subproblems
- P381: Runtime focused finalize regression tests
- P382: Runtime finalize source guard classification

## Results
- R365

## Latest Check
C388

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P378/README.md
- Ticket T369: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P378/tickets/T369.md
- Result R365: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P378/results/R365.md
- Check C388: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P378/checks/C388.md

## Follow-ups
- none
