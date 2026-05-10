# P052: Phase 5B3.1 Compatibility Residue Audit Map

Status: done
Parent: P051
Root: P000
Package: problems/P000/children/P006/children/P046/children/P051/children/P052
Body: problems/P000/children/P006/children/P046/children/P051/children/P052/README.md
Ticket(s): T050

## Problem
Before deleting or renaming compatibility wrappers, we need a precise source/test inventory of `compat`, `compatibility`, `legacy`, `fallback`, and broad projection helpers. The current hit list mixes legitimate schema migrations, guard tests, current adapters, stale comments, and potentially removable wrappers.

## Success Criteria
- Record a categorized audit of all relevant Cortex source/test hits.
- Identify which hits are legitimate current mechanisms and which require deletion/rename.
- Specifically classify `step_result_projection.format_for_llm`, `novaic_cortex.__init__` exports, and tests importing broad projection helpers.
- Produce a concrete execution map for the following cleanup child problems.
- No source code changes are required beyond the result artifact for this audit problem.

## Subproblems
- none

## Results
- R046

## Latest Check
C049

## Bodies
- Problem: problems/P000/children/P006/children/P046/children/P051/children/P052/README.md
- Ticket T050: problems/P000/children/P006/children/P046/children/P051/children/P052/tickets/T050.md
- Result R046: problems/P000/children/P006/children/P046/children/P051/children/P052/results/R046.md
- Check C049: problems/P000/children/P006/children/P046/children/P051/children/P052/checks/C049.md

## Follow-ups
- none
