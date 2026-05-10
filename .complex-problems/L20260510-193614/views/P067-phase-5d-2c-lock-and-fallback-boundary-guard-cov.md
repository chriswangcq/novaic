# P067: Phase 5D.2c Lock And Fallback Boundary Guard Coverage

Status: done
Parent: P062
Root: P000
Package: problems/P000/children/P006/children/P048/children/P062/children/P067
Body: problems/P000/children/P006/children/P048/children/P062/children/P067/README.md
Ticket(s): T065

## Problem
Review and, if needed, tighten guard tests for production lock/fallback boundaries: Cortex must fail closed without a production scope lock backend, process memory must not be described as authority, and removed compatibility wrappers must stay removed.

This belongs under P062 because lock/fallback boundaries are independent from scope projection and step formatting contracts.

## Success Criteria
- Identify tests or startup checks covering Redis scope lock production installation/fail-closed behavior.
- Identify tests or static checks covering removal of `format_for_llm` public compatibility wrapper.
- Identify tests/static checks covering no `scope_state_log` authority path.
- Run relevant tests or add missing guards.

## Subproblems
- none

## Results
- R061

## Latest Check
C065

## Bodies
- Problem: problems/P000/children/P006/children/P048/children/P062/children/P067/README.md
- Ticket T065: problems/P000/children/P006/children/P048/children/P062/children/P067/tickets/T065.md
- Result R061: problems/P000/children/P006/children/P048/children/P062/children/P067/results/R061.md
- Check C065: problems/P000/children/P006/children/P048/children/P062/children/P067/checks/C065.md

## Follow-ups
- none
