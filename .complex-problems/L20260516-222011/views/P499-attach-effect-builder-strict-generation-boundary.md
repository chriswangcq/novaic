# P499: Attach effect builder strict generation boundary

Status: done
Parent: P497
Root: P000
Source Ticket: T489 (split)
Source Check: none
Package: problems/P000/children/P004/children/P279/children/P482/children/P490/children/P497/children/P499
Body: problems/P000/children/P004/children/P279/children/P482/children/P490/children/P497/children/P499/README.md
Ticket(s): T490

## Problem
`build_attach_input_effect()` still accepts an optional `expected_session_generation`, which makes the attach effect construction boundary weaker than the runtime handler and outbox publisher boundaries. The builder should reject missing or invalid generation values before constructing a `SESSION_ATTACH_INPUT` effect.

## Success Criteria
- `build_attach_input_effect()` requires and validates a positive explicit `expected_session_generation`.
- The builder reuses the existing session generation contract helper instead of duplicating validation.
- Focused tests prove missing, bool, zero, and invalid generation values are rejected at the builder boundary.
- Valid attach effects keep the existing payload shape with `expected_wake_scope_id` and positive integer `expected_session_generation`.

## Subproblems
- none

## Results
- R484

## Latest Check
C513

## Bodies
- Problem: problems/P000/children/P004/children/P279/children/P482/children/P490/children/P497/children/P499/README.md
- Ticket T490: problems/P000/children/P004/children/P279/children/P482/children/P490/children/P497/children/P499/tickets/T490.md
- Result R484: problems/P000/children/P004/children/P279/children/P482/children/P490/children/P497/children/P499/results/R484.md
- Check C513: problems/P000/children/P004/children/P279/children/P482/children/P490/children/P497/children/P499/checks/C513.md

## Follow-ups
- none
