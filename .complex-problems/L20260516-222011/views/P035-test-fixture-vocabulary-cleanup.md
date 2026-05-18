# P035: Test fixture vocabulary cleanup

Status: done
Parent: P033
Root: P000
Source Ticket: T025 (split)
Source Check: none
Package: problems/P000/children/P001/children/P009/children/P015/children/P033/children/P035
Body: problems/P000/children/P001/children/P009/children/P015/children/P033/children/P035/README.md
Ticket(s): T027

## Problem
Several tests still use direct-tool names as generic examples. Some are valid legacy regression tests, but current-contract tests should use final harness tools or shell-first examples.

## Success Criteria
- Replace generic current-contract fixtures using `im_read`, `im_reply`, payload tools, `audio_qa`, or `subagent_spawn`.
- Rename unavoidable legacy fixtures/helpers to make legacy intent explicit.
- Preserve regression coverage for old archived step data.
- Run focused test files for changed tests.

## Subproblems
- P038: Common contract test fixtures
- P039: Runtime test fixtures
- P040: Cortex test fixtures
- P041: App monitor test fixtures

## Results
- R030

## Latest Check
C039

## Bodies
- Problem: problems/P000/children/P001/children/P009/children/P015/children/P033/children/P035/README.md
- Ticket T027: problems/P000/children/P001/children/P009/children/P015/children/P033/children/P035/tickets/T027.md
- Result R030: problems/P000/children/P001/children/P009/children/P015/children/P033/children/P035/results/R030.md
- Check C039: problems/P000/children/P001/children/P009/children/P015/children/P033/children/P035/checks/C039.md

## Follow-ups
- none
