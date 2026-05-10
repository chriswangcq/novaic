# P064: Phase 5D.4 Full Cortex Test And PyCompile Gate

Status: done
Parent: P048
Root: P000
Package: problems/P000/children/P006/children/P048/children/P064
Body: problems/P000/children/P006/children/P048/children/P064/README.md
Ticket(s): T067

## Problem
Run the full `novaic-cortex/tests` suite and Cortex module `py_compile` after static and targeted verification. This is the final broad behavior gate for Phase 5 cleanup.

This belongs under P048 because full-suite verification is independently expensive and should not be hidden inside a vague one-go result.

## Success Criteria
- Run `python3 -m py_compile` across `novaic-cortex/novaic_cortex`.
- Run full `pytest -q novaic-cortex/tests`.
- Record exact command outputs.
- If failures occur, triage whether they are caused by this remediation chain, pre-existing unrelated failures, or environment issues; create follow-up work for caused failures.

## Subproblems
- none

## Results
- R064

## Latest Check
C068

## Bodies
- Problem: problems/P000/children/P006/children/P048/children/P064/README.md
- Ticket T067: problems/P000/children/P006/children/P048/children/P064/tickets/T067.md
- Result R064: problems/P000/children/P006/children/P048/children/P064/results/R064.md
- Check C068: problems/P000/children/P006/children/P048/children/P064/checks/C068.md

## Follow-ups
- none
