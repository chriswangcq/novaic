# P820: Queue service residual standalone entrypoint audit

Status: done
Parent: P698
Root: P000
Source Ticket: T814 (split)
Source Check: none
Package: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P698/children/P820
Body: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P698/children/P820/README.md
Ticket(s): T815

## Problem
`novaic-agent-runtime/queue_service/main.py` is a standalone FastAPI app with `if __name__` block. All launch scripts use `main_novaic.py queue-service` instead. Determine if queue_service/main.py is needed for direct testing or is dead code.

## Success Criteria
- queue_service/main.py is classified as active (with rationale) or deleted.
- If deleted, no import or test references break.
- Relevant tests pass.

## Subproblems
- none

## Results
- R809

## Latest Check
C858

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P698/children/P820/README.md
- Ticket T815: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P698/children/P820/tickets/T815.md
- Result R809: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P698/children/P820/results/R809.md
- Check C858: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P698/children/P820/checks/C858.md

## Follow-ups
- none
