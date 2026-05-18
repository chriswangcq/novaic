# P401: Widened guard residue matrix

Status: done
Parent: P398
Root: P000
Source Ticket: T389 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/children/P389/children/P398/children/P401
Body: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/children/P389/children/P398/children/P401/README.md
Ticket(s): T392

## Problem
The widened guard still reports many generation-like, round, retry, and counter defaults across runtime and Cortex code. Some are harmless counters, but the project needs a final explicit matrix proving no live generation authority residue remains.

## Success Criteria
- Rerun the widened guard after the live-boundary children are complete.
- Classify every remaining hit into live session authority, event sequencing, round number, retry/health counter, persistence/audit adapter, or generic non-session counter.
- Patch any remaining live authority hit discovered by the matrix.
- Provide a concise matrix in the result with file evidence.
- Rerun narrow guard and focused tests; no unclassified residue remains.

## Subproblems
- none

## Results
- R384

## Latest Check
C407

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/children/P389/children/P398/children/P401/README.md
- Ticket T392: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/children/P389/children/P398/children/P401/tickets/T392.md
- Result R384: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/children/P389/children/P398/children/P401/results/R384.md
- Check C407: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/children/P389/children/P398/children/P401/checks/C407.md

## Follow-ups
- none
