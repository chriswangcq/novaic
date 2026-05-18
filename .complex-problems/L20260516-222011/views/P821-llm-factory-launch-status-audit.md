# P821: LLM factory launch status audit

Status: done
Parent: P698
Root: P000
Source Ticket: T814 (split)
Source Check: none
Package: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P698/children/P821
Body: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P698/children/P821/README.md
Ticket(s): T816

## Problem
`novaic-llm-factory` has its own `main.py` (port 9100) and `factory/app.py` but is absent from all three launch scripts. It appears to be an orphaned service entrypoint.

## Success Criteria
- llm-factory launch status is classified: should it be in start.sh, or is it intentionally standalone/manual-only?
- If it should be orchestrated, a follow-up is recorded. If standalone is intentional, this is documented.
- No stale references to llm-factory in launch scripts.

## Subproblems
- none

## Results
- R810

## Latest Check
C859

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P698/children/P821/README.md
- Ticket T816: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P698/children/P821/tickets/T816.md
- Result R810: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P698/children/P821/results/R810.md
- Check C859: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P698/children/P821/checks/C859.md

## Follow-ups
- none
