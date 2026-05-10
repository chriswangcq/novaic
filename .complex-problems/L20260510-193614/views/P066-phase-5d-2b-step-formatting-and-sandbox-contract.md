# P066: Phase 5D.2b Step Formatting And Sandbox Contract Guard Coverage

Status: done
Parent: P062
Root: P000
Package: problems/P000/children/P006/children/P048/children/P062/children/P066
Body: problems/P000/children/P006/children/P048/children/P062/children/P066/README.md
Ticket(s): T064

## Problem
Review and, if needed, tighten guards for public step formatting and sandbox path contracts: public step formatting must use explicit `projection`, and temp sandbox backing paths must remain rejected.

This belongs under P062 because step formatting/sandbox contracts are independent from scope authority.

## Success Criteria
- Identify tests covering unsupported step projection and absence of public `include_display`.
- Identify tests covering stable `/cortex/ro` / `/cortex/rw` guidance and rejection of `novaic-cortex-sandbox-*` backing paths.
- Run the relevant tests or add missing guards.
- Classify low-level `include_display` resolver internals separately from public API.

## Subproblems
- none

## Results
- R060

## Latest Check
C064

## Bodies
- Problem: problems/P000/children/P006/children/P048/children/P062/children/P066/README.md
- Ticket T064: problems/P000/children/P006/children/P048/children/P062/children/P066/tickets/T064.md
- Result R060: problems/P000/children/P006/children/P048/children/P062/children/P066/results/R060.md
- Check C064: problems/P000/children/P006/children/P048/children/P062/children/P066/checks/C064.md

## Follow-ups
- none
