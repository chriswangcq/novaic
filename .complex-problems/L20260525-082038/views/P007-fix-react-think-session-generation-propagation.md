# P007: Fix react_think session_generation propagation

Status: doing
Parent: P006
Root: P000
Source Ticket: none (none)
Source Check: C004
Package: problems/P000/children/P003/children/P006/children/P007
Body: problems/P000/children/P003/children/P006/children/P007/README.md
Ticket(s): T007

## Problem
The recovered production message path reaches Queue and starts `react_think`, but the initial `react_think` context created by `subagent_wake` does not include the required `session_generation`. Runtime fails at `cortex.prepare_llm_context` with `ReactThinkInput.session_generation is required`, so users still see sent messages with no response.

## Success Criteria
- `subagent_wake` includes a positive `session_generation` in the initial `react_think` trigger context.
- Missing or invalid `session_generation` still fails fast instead of using a fallback/default.
- Runtime unit tests cover the initial wake-to-think propagation.
- Fixed code is committed, pushed, deployed through Release Controller to staging and prod.
- Production verification shows a new user message no longer fails with `ReactThinkInput.session_generation is required` and reaches the next response stage.

## Subproblems
- none

## Results
- none

## Latest Check
none

## Bodies
- Problem: problems/P000/children/P003/children/P006/children/P007/README.md
- Ticket T007: problems/P000/children/P003/children/P006/children/P007/tickets/T007.md

## Follow-ups
- none
