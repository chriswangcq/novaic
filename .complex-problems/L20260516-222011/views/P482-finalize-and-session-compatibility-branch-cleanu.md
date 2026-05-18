# P482: Finalize and session compatibility branch cleanup

Status: done
Parent: P279
Root: P000
Source Ticket: T474 (split)
Source Check: none
Package: problems/P000/children/P004/children/P279/children/P482
Body: problems/P000/children/P004/children/P279/children/P482/README.md
Ticket(s): T481

## Problem
Finalize, session-ended, attach, and recovery paths are especially sensitive after the FSM migration. P279 needs old compatibility/fallback branches in these paths reviewed, and high-confidence stale branches removed or converted to explicit generation/FSM behavior.

## Success Criteria
- Finalize/session-ended/attach/recovery paths are scanned for legacy, compat, fallback, missing-generation, stale-generation, and direct mutation language.
- Retained branches are classified as active required path, guard/test fixture, or adapter boundary.
- High-confidence stale compatibility branches are removed or tightened.
- Ambiguous branches become child follow-up problems rather than speculative edits.
- Focused finalize/session runtime tests pass after any source change.

## Subproblems
- P488: Finalize/session compatibility residue inventory
- P489: Finalize ownership cleanup
- P490: Attach generation compatibility cleanup
- P491: Recovery and session-ended compatibility cleanup
- P492: Final finalize/session compatibility verification

## Results
- R494

## Latest Check
C523

## Bodies
- Problem: problems/P000/children/P004/children/P279/children/P482/README.md
- Ticket T481: problems/P000/children/P004/children/P279/children/P482/tickets/T481.md
- Result R494: problems/P000/children/P004/children/P279/children/P482/results/R494.md
- Check C523: problems/P000/children/P004/children/P279/children/P482/checks/C523.md

## Follow-ups
- none
