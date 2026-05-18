# P505: Final imperative dispatch residue cleanup

Status: done
Parent: P483
Root: P000
Source Ticket: T498 (split)
Source Check: none
Package: problems/P000/children/P004/children/P279/children/P483/children/P505
Body: problems/P000/children/P004/children/P279/children/P483/children/P505/README.md
Ticket(s): T500

## Problem
The final guard classification may uncover high-confidence stale production residue or ambiguous dispatch/session compatibility branches. P483 needs a dedicated cleanup child so any source changes are scoped, testable, and not mixed into the inventory step.

## Success Criteria
- High-confidence stale production residue from the final classification is removed or tightened.
- Required adapter/outbox/FSM boundaries are retained and documented instead of deleted.
- Ambiguous production hits are split into follow-up problems if they cannot be safely fixed directly.
- Focused tests covering any changed source path pass.
- A diff artifact records exactly what changed, or explicitly states no source cleanup was needed after classification.

## Subproblems
- none

## Results
- R496

## Latest Check
C525

## Bodies
- Problem: problems/P000/children/P004/children/P279/children/P483/children/P505/README.md
- Ticket T500: problems/P000/children/P004/children/P279/children/P483/children/P505/tickets/T500.md
- Result R496: problems/P000/children/P004/children/P279/children/P483/children/P505/results/R496.md
- Check C525: problems/P000/children/P004/children/P279/children/P483/children/P505/checks/C525.md

## Follow-ups
- none
