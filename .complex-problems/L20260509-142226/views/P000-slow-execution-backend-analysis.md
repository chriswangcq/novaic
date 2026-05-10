# P000: Slow execution backend analysis

Status: done
Parent: none
Root: P000
Package: problems/P000
Body: problems/P000/README.md
Ticket(s): T000

## Problem
User reports execution is slow after deploying and testing Host Desktop device tools. Need inspect backend evidence instead of guessing, determine where latency is introduced, and explain root cause or likely bottleneck with concrete pointers.

## Success Criteria
- Identify whether recent slowness is in queue scheduling, Runtime worker execution, LLM/Cortex context preparation, Device proxy/PC client, or logging/IO.
- Use backend evidence from production status, task DB/logs, or remote smoke timing.
- Avoid scanning huge logs naively; use bounded queries and narrow time windows.
- Record evidence and residual uncertainty in a solve-complex-problems ledger.

## Subproblems
- none

## Results
- R000

## Latest Check
C000

## Bodies
- Problem: problems/P000/README.md
- Ticket T000: problems/P000/tickets/T000.md
- Result R000: problems/P000/results/R000.md
- Check C000: problems/P000/checks/C000.md

## Follow-ups
- none
