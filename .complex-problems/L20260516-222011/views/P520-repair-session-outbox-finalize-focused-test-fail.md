# P520: Repair Session Outbox Finalize Focused Test Failures

Status: done
Parent: P517
Root: P000
Source Ticket: none (none)
Source Check: C540
Package: problems/P000/children/P004/children/P281/children/P511/children/P517/children/P520
Body: problems/P000/children/P004/children/P281/children/P511/children/P517/children/P520/README.md
Ticket(s): T514

## Problem
The P517 focused pytest subset failed in three tests covering recovery remaining-stack semantics, attach outbox published status, and session repository wrapper-boundary expectations.

## Success Criteria
- Understand whether each failure is a production bug or stale test expectation.
- Apply the minimal correct code/test updates.
- Rerun the failing tests and the P517 focused subset successfully.
- Record exact files changed, commands, and counts.

## Subproblems
- P521: Repair Recovery Remaining Stack Failure
- P522: Repair Attach Outbox Published Status Failure
- P523: Repair Session Repository Wrapper Boundary Count Failure
- P524: Rerun Full Session Outbox Finalize Focused Subset

## Results
- R513

## Latest Check
C546

## Bodies
- Problem: problems/P000/children/P004/children/P281/children/P511/children/P517/children/P520/README.md
- Ticket T514: problems/P000/children/P004/children/P281/children/P511/children/P517/children/P520/tickets/T514.md
- Result R513: problems/P000/children/P004/children/P281/children/P511/children/P517/children/P520/results/R513.md
- Check C544: problems/P000/children/P004/children/P281/children/P511/children/P517/children/P520/checks/C544.md
- Check C546: problems/P000/children/P004/children/P281/children/P511/children/P517/children/P520/checks/C546.md

## Follow-ups
- P524: Rerun Full Session Outbox Finalize Focused Subset
