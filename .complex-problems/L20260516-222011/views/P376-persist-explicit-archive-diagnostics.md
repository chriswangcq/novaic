# P376: Persist Explicit Archive Diagnostics

Status: done
Parent: P373
Root: P000
Source Ticket: T362 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P338/children/P368/children/P373/children/P376
Body: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P338/children/P368/children/P373/children/P376/README.md
Ticket(s): T364

## Problem
Implement explicit finalize diagnostics persistence in Cortex without conflating it with semantic remaining-stack lifecycle data.

## Success Criteria
- Diagnostic archive requests persist explicit `session_generation`, `finalize_reason`, diagnostic `remaining_stack`, and `round_num` in durable context-event metadata.
- Pure structural Cortex scope-end callers without diagnostics keep existing event payload shape.
- The implementation uses only `ScopeEndRequest` diagnostics for diagnostic metadata and does not synthesize generation from active state.
- Focused Cortex tests pass.

## Subproblems
- none

## Results
- R356

## Latest Check
C379

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P338/children/P368/children/P373/children/P376/README.md
- Ticket T364: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P338/children/P368/children/P373/children/P376/tickets/T364.md
- Result R356: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P338/children/P368/children/P373/children/P376/results/R356.md
- Check C379: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P338/children/P368/children/P373/children/P376/checks/C379.md

## Follow-ups
- none
