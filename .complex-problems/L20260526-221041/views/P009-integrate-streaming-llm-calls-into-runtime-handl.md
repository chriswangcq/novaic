# P009: Integrate streaming LLM calls into Runtime handler

Status: done
Parent: P002
Root: P000
Source Ticket: T004 (split)
Source Check: none
Package: problems/P000/children/P002/children/P009
Body: problems/P000/children/P002/children/P009/README.md
Ticket(s): T007

## Problem
`handle_llm_call` must request streaming from Factory, feed reasoning deltas to the projection helper, and still return the same complete response shape expected by `react_think` and context append.

## Success Criteria
- Handler uses streaming client path for supported Factory calls.
- Handler coalesces projection updates and finalizes reasoning when the stream completes.
- Handler returns `success`, `scope_id`, `round_id`, `response`, and `model` as before.
- Tests prove saga-facing response compatibility and non-streaming/failure behavior remains clear.

## Subproblems
- none

## Results
- R005

## Latest Check
C005

## Bodies
- Problem: problems/P000/children/P002/children/P009/README.md
- Ticket T007: problems/P000/children/P002/children/P009/tickets/T007.md
- Result R005: problems/P000/children/P002/children/P009/results/R005.md
- Check C005: problems/P000/children/P002/children/P009/checks/C005.md

## Follow-ups
- none
