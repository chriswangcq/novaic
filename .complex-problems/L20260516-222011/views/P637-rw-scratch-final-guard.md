# P637: RW Scratch Final Guard

Status: done
Parent: P631
Root: P000
Source Ticket: T630 (split)
Source Check: none
Package: problems/P000/children/P005/children/P554/children/P631/children/P637
Body: problems/P000/children/P005/children/P554/children/P631/children/P637/README.md
Ticket(s): T639

## Problem
The cleanup needs a final skeptical pass to ensure root `/rw/scratch` is no longer advertised as the preferred/default scratch contract while legitimate arbitrary RW paths and lower-layer tests remain intentional.

## Success Criteria
- Post-change scans classify all remaining `/rw/scratch` hits.
- Focused tests pass.
- Any remaining root `/rw/scratch` hit is explicitly justified or converted into a follow-up.

## Subproblems
- P644: Final RW Scratch Residue Scan Classification
- P645: Final RW Scratch Focused Verification

## Results
- R637

## Latest Check
C678

## Bodies
- Problem: problems/P000/children/P005/children/P554/children/P631/children/P637/README.md
- Ticket T639: problems/P000/children/P005/children/P554/children/P631/children/P637/tickets/T639.md
- Result R637: problems/P000/children/P005/children/P554/children/P631/children/P637/results/R637.md
- Check C678: problems/P000/children/P005/children/P554/children/P631/children/P637/checks/C678.md

## Follow-ups
- none
