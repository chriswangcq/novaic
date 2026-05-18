# P214: Audit projection guard test labels and assertions

Status: done
Parent: P200
Root: P000
Source Ticket: T202 (split)
Source Check: none
Package: problems/P000/children/P003/children/P127/children/P187/children/P200/children/P214
Body: problems/P000/children/P003/children/P127/children/P187/children/P200/children/P214/README.md
Ticket(s): T204

## Problem
Some tests intentionally feed historical or malformed inputs to prove they do not leak images. These should remain, but their names/assertions should read as guardrails, not endorsement of legacy contracts.

## Success Criteria
- Projection guard tests are inspected for misleading legacy naming.
- Any confusing test names or assertions are rewritten.
- Tests that remain clearly express the desired contract.

## Subproblems
- none

## Results
- R199

## Latest Check
C213

## Bodies
- Problem: problems/P000/children/P003/children/P127/children/P187/children/P200/children/P214/README.md
- Ticket T204: problems/P000/children/P003/children/P127/children/P187/children/P200/children/P214/tickets/T204.md
- Result R199: problems/P000/children/P003/children/P127/children/P187/children/P200/children/P214/results/R199.md
- Check C213: problems/P000/children/P003/children/P127/children/P187/children/P200/children/P214/checks/C213.md

## Follow-ups
- none
