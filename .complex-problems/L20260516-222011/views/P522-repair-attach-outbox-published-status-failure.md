# P522: Repair Attach Outbox Published Status Failure

Status: done
Parent: P520
Root: P000
Source Ticket: T514 (split)
Source Check: none
Package: problems/P000/children/P004/children/P281/children/P511/children/P517/children/P520/children/P522
Body: problems/P000/children/P004/children/P281/children/P511/children/P517/children/P520/children/P522/README.md
Ticket(s): T516

## Problem
`test_outbox_records_start_and_published_attach_effects_after_cutover` expects attach outbox effect status `published`, but current behavior leaves it `pending`.

## Success Criteria
- Determine whether attach effects should be auto-published in this test setup or remain pending for worker dispatch.
- Apply minimal correct code/test update.
- Rerun the failing test successfully.

## Subproblems
- none

## Results
- R511

## Latest Check
C542

## Bodies
- Problem: problems/P000/children/P004/children/P281/children/P511/children/P517/children/P520/children/P522/README.md
- Ticket T516: problems/P000/children/P004/children/P281/children/P511/children/P517/children/P520/children/P522/tickets/T516.md
- Result R511: problems/P000/children/P004/children/P281/children/P511/children/P517/children/P520/children/P522/results/R511.md
- Check C542: problems/P000/children/P004/children/P281/children/P511/children/P517/children/P520/children/P522/checks/C542.md

## Follow-ups
- none
