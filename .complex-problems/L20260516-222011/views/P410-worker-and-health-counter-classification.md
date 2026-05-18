# P410: Worker and health counter classification

Status: done
Parent: P403
Root: P000
Source Ticket: T395 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P403/children/P410
Body: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P403/children/P410/README.md
Ticket(s): T403

## Problem
Worker and health files contain many `or 0` retry/count/status patterns. These are likely non-session counters, but they should be explicitly classified so the final compatibility audit does not hide live session residue among noisy worker metrics.

## Success Criteria
- Inspect worker/health/task execution hits from P402.
- Classify each hit as retry/counter/status-code state or patch it if it affects session mutation.
- Verify no worker counter path writes attach/finalize/session-ended generation authority.
- Add tests only if a live boundary is changed.
- Record the classification matrix for final verification.

## Subproblems
- none

## Results
- R397

## Latest Check
C423

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P403/children/P410/README.md
- Ticket T403: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P403/children/P410/tickets/T403.md
- Result R397: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P403/children/P410/results/R397.md
- Check C423: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P403/children/P410/checks/C423.md

## Follow-ups
- none
