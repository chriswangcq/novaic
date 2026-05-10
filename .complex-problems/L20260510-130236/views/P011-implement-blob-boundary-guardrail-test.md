# P011: Implement Blob Boundary Guardrail Test

Status: done
Parent: P007
Root: P000
Package: problems/P000/children/P004/children/P007/children/P011
Body: problems/P000/children/P004/children/P007/children/P011/README.md
Ticket(s): T008

## Problem
The repository needs an automated guardrail that fails when live Cortex `RO` / `RW` code reintroduces direct Blob object-store authority outside the narrow file authority boundary. The guardrail must be precise enough to permit legitimate Blob byte flows.

This child belongs under T006 because it turns the allowlist into executable protection.

## Success Criteria
- A targeted test or CI-accessible script scans source files for forbidden Blob object-store bypass patterns.
- The scanner uses the allowlist from the previous child problem.
- The scanner is checked into the repo and runs in a targeted test command.
- Current allowed Blob byte flows pass the guardrail.

## Subproblems
- none

## Results
- R005

## Latest Check
C005

## Bodies
- Problem: problems/P000/children/P004/children/P007/children/P011/README.md
- Ticket T008: problems/P000/children/P004/children/P007/children/P011/tickets/T008.md
- Result R005: problems/P000/children/P004/children/P007/children/P011/results/R005.md
- Check C005: problems/P000/children/P004/children/P007/children/P011/checks/C005.md

## Follow-ups
- none
