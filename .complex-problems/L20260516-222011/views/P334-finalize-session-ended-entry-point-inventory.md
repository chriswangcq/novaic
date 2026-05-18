# P334: Finalize/session-ended entry-point inventory

Status: done
Parent: P328
Root: P000
Source Ticket: T324 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P334
Body: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P334/README.md
Ticket(s): T325

## Problem
All finalize, session-ended, watchdog, recovery, restart, and skill-end entry points must be enumerated before changing behavior. The current risk is hidden entry points clearing active session state without carrying or checking the intended generation.

## Success Criteria
- List every finalize/session-ended/recovery/watchdog/restart/skill-end entry point with file references.
- For each entry point, record whether it carries saga id, wake scope id, session generation, reason, remaining stack, pending input ids, and restart intent.
- Classify each entry point as safe, unsafe, or needing downstream child audit.
- Identify test files that currently exercise each entry point.
- Produce follow-up targets for any path that is not explicitly generation-checked.

## Subproblems
- none

## Results
- R320

## Latest Check
C341

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P334/README.md
- Ticket T325: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P334/tickets/T325.md
- Result R320: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P334/results/R320.md
- Check C341: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P334/checks/C341.md

## Follow-ups
- none
