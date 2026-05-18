# P328: Finalize and session-ended generation ownership audit

Status: done
Parent: P283
Root: P000
Source Ticket: T317 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P328
Body: problems/P000/children/P004/children/P278/children/P283/children/P328/README.md
Ticket(s): T324

## Problem
Audit finalize/session-ended paths to verify they close or advance only the intended session generation and cannot clear a newer active session because of stale saga completion, watchdog, recovery, or nested skill closure behavior.

## Success Criteria
- Map all finalize/session-ended entry points and the generation/session keys they carry.
- Verify current-generation checks before clearing active state, restarting pending input, or archiving remaining stack.
- Identify whether remaining stack and reason are recorded at the generation boundary.
- Add or identify tests proving stale finalize/session-ended events do not close the wrong active generation.

## Subproblems
- P334: Finalize/session-ended entry-point inventory
- P335: Repository finalize generation atomicity
- P336: Session-ended outbox delivery generation contract
- P337: Runtime session-ended handler enforcement
- P338: Remaining stack and finalize reason archive boundary
- P339: Finalize generation aggregate regression coverage

## Results
- R388

## Latest Check
C414

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P328/README.md
- Ticket T324: problems/P000/children/P004/children/P278/children/P283/children/P328/tickets/T324.md
- Result R388: problems/P000/children/P004/children/P278/children/P283/children/P328/results/R388.md
- Check C414: problems/P000/children/P004/children/P278/children/P283/children/P328/checks/C414.md

## Follow-ups
- none
