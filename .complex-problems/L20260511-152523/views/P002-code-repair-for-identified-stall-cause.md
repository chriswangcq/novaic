# P002: Code repair for identified stall cause

Status: done
Parent: P000
Root: P000
Package: problems/P000/children/P002
Body: problems/P000/children/P002/README.md
Ticket(s): T002

## Problem
Implement the smallest deterministic code change that fixes the root cause discovered in live diagnosis. Avoid compatibility fallbacks or masking behavior; the repaired harness should progress or fail explicitly.

## Success Criteria
- The responsible module is patched.
- Regression tests cover the failing transition or state.
- Local targeted tests pass.
- The diff is reviewed for hidden fallback, stale branch, or unclear dependency boundary.

## Subproblems
- P004: Shell capability Cortex internal auth repair
- P005: Tool result step_ref projection repair
- P006: Wake finalize compensation context repair

## Results
- R004

## Latest Check
C004

## Bodies
- Problem: problems/P000/children/P002/README.md
- Ticket T002: problems/P000/children/P002/tickets/T002.md
- Result R004: problems/P000/children/P002/results/R004.md
- Check C004: problems/P000/children/P002/checks/C004.md

## Follow-ups
- none
