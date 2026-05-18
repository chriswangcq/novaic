# P610: Fix Runtime Projection Session Generation Test Fixtures

Status: done
Parent: P608
Root: P000
Source Ticket: none (none)
Source Check: C633
Package: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P583/children/P601/children/P604/children/P608/children/P610
Body: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P583/children/P601/children/P604/children/P608/children/P610/README.md
Ticket(s): T602

## Problem
The P608 artifact/image rendering audit found that the targeted Cortex/runtime projection test suite is not fully clean because two legacy tests in `novaic-agent-runtime/tests/test_pr71_no_tool_retry_context_cleanup.py` construct React saga contexts without the required explicit `session_generation`. This blocks P608 closure even though the artifact/image projection behavior itself appears mostly sound.

## Success Criteria
- Update the minimal outdated test fixtures or helper builders so the tests use explicit positive `session_generation` values that match the current runtime contract.
- Re-run the targeted Cortex/runtime artifact projection tests and record a clean pass.
- Confirm the fix does not loosen production generation requirements and does not add compatibility fallback code for missing generation.

## Subproblems
- none

## Results
- R594

## Latest Check
C634

## Bodies
- Problem: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P583/children/P601/children/P604/children/P608/children/P610/README.md
- Ticket T602: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P583/children/P601/children/P604/children/P608/children/P610/tickets/T602.md
- Result R594: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P583/children/P601/children/P604/children/P608/children/P610/results/R594.md
- Check C634: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P583/children/P601/children/P604/children/P608/children/P610/checks/C634.md

## Follow-ups
- none
