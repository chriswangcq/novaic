# P339: Finalize generation aggregate regression coverage

Status: done
Parent: P328
Root: P000
Source Ticket: T324 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339
Body: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/README.md
Ticket(s): T368

## Problem
After the targeted finalize/session-ended fixes, aggregate tests and source guards must prove the full boundary is closed and no stale compatibility residue remains.

## Success Criteria
- Build a matrix covering repository, outbox, runtime handler, remaining-stack archive, watchdog/recovery, and restart paths.
- Run focused pytest suites covering session FSM, outbox, recovery, generation checks, and legacy cleanup.
- Run source guards for missing generation defaults, direct active clear helpers, and stale fallback generation behavior.
- Record any uncovered path as a new follow-up child problem rather than declaring success.
- Close only when stale finalize/session-ended cannot clear, restart, or archive a newer active generation.

## Subproblems
- P378: Runtime finalize generation aggregate regression
- P379: Cortex archive diagnostics aggregate regression
- P380: Cross-repo stale compatibility residue guard

## Results
- R387

## Latest Check
C413

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/README.md
- Ticket T368: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/tickets/T368.md
- Result R387: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/results/R387.md
- Check C413: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/checks/C413.md

## Follow-ups
- none
