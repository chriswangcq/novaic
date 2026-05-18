# P480: Imperative dispatch residue inventory

Status: done
Parent: P279
Root: P000
Source Ticket: T474 (split)
Source Check: none
Package: problems/P000/children/P004/children/P279/children/P480
Body: problems/P000/children/P004/children/P279/children/P480/README.md
Ticket(s): T475

## Problem
P279 needs a focused inventory of old imperative dispatch, fallback, legacy, compatibility, direct saga creation, direct session mutation, and finalize/session-ended branches before deletion decisions are made. Without a saved inventory, cleanup can become speculative and easy to under- or over-delete.

## Success Criteria
- Saved guard artifact lists searched patterns and matching files.
- Each hit bucket is classified as required boundary, test/docs guard, high-confidence removable residue, or ambiguous follow-up candidate.
- The inventory records enough file references for downstream cleanup children to act without re-discovering the whole surface.
- No production code is changed in this inventory child.

## Subproblems
- none

## Results
- R472

## Latest Check
C501

## Bodies
- Problem: problems/P000/children/P004/children/P279/children/P480/README.md
- Ticket T475: problems/P000/children/P004/children/P279/children/P480/tickets/T475.md
- Result R472: problems/P000/children/P004/children/P279/children/P480/results/R472.md
- Check C501: problems/P000/children/P004/children/P279/children/P480/checks/C501.md

## Follow-ups
- none
