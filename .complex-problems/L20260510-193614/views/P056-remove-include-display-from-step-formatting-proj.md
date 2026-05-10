# P056: Remove include_display From Step Formatting Projection API

Status: done
Parent: P055
Root: P000
Package: problems/P000/children/P006/children/P046/children/P051/children/P055/children/P056
Body: problems/P000/children/P006/children/P046/children/P051/children/P055/children/P056/README.md
Ticket(s): T054

## Problem
The step-result formatting path still carries `include_display` as a boolean projection selector across runtime and Cortex. This is a compatibility-style API that conflicts with the explicit projection-mode contract.

## Success Criteria
- Remove `include_display` from `StepFormattedRequest`.
- Remove the unknown/empty projection branch that chooses display/history via `include_display`; unsupported projections should fail explicitly or all callers should pass a valid projection.
- Remove `include_display` from `CortexBridge.read_step_formatted`, `expand_step_ref_to_content`, and `fetch_step_for_llm`.
- Update `expand_messages_for_llm` to pass only explicit `projection`.
- Update runtime/Cortex tests to assert projection-only payloads and behavior.
- Static search shows `include_display` no longer appears in step formatting request/client paths except in `resolve_for_llm`, where it is a different byte-resolution option.
- Targeted runtime and Cortex tests pass.

## Subproblems
- none

## Results
- R050

## Latest Check
C053

## Bodies
- Problem: problems/P000/children/P006/children/P046/children/P051/children/P055/children/P056/README.md
- Ticket T054: problems/P000/children/P006/children/P046/children/P051/children/P055/children/P056/tickets/T054.md
- Result R050: problems/P000/children/P006/children/P046/children/P051/children/P055/children/P056/results/R050.md
- Check C053: problems/P000/children/P006/children/P046/children/P051/children/P055/children/P056/checks/C053.md

## Follow-ups
- none
