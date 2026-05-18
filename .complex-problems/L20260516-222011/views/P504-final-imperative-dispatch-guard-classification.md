# P504: Final imperative dispatch guard classification

Status: done
Parent: P483
Root: P000
Source Ticket: T498 (split)
Source Check: none
Package: problems/P000/children/P004/children/P279/children/P483/children/P504
Body: problems/P000/children/P004/children/P279/children/P483/children/P504/README.md
Ticket(s): T499

## Problem
P483 needs a fresh, saved guard sweep after all previous cleanup children. Without a final classification artifact, the parent cannot prove whether remaining direct dispatch, fallback, compatibility, or finalize/session hits are production residue or intentional guard/test references.

## Success Criteria
- Saved raw guard output covers direct saga creation, direct queue publish, legacy/fallback/compat dispatch terms, active-session pointer usage, attach generation bypasses, and finalize/session-ended compatibility terms.
- Every production hit is classified with a concrete file/path reference.
- Test/docs guard hits are separated from production hits.
- Any production hit that cannot be confidently classified is recorded as a follow-up candidate for the next child.
- No production code is changed in this inventory/classification child.

## Subproblems
- none

## Results
- R495

## Latest Check
C524

## Bodies
- Problem: problems/P000/children/P004/children/P279/children/P483/children/P504/README.md
- Ticket T499: problems/P000/children/P004/children/P279/children/P483/children/P504/tickets/T499.md
- Result R495: problems/P000/children/P004/children/P279/children/P483/children/P504/results/R495.md
- Check C524: problems/P000/children/P004/children/P279/children/P483/children/P504/checks/C524.md

## Follow-ups
- none
