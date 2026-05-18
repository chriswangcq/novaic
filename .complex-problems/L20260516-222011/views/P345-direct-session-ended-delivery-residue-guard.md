# P345: Direct session-ended delivery residue guard

Status: done
Parent: P343
Root: P000
Source Ticket: T331 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P336/children/P343/children/P345
Body: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P336/children/P343/children/P345/README.md
Ticket(s): T332

## Problem
The direct P336 delivery boundary must be free of generation-zero compatibility code after P341/P342. Verify and remove any remaining fallback/defaulting in `wake_finalize`, `session_handlers`, `SagaClient.session_ended`, and `SessionEndedRequest`.

## Success Criteria
- Source search proves the direct delivery boundary has no `session_generation or 0`, `if generation is None`-only validation, or plain non-positive route schema.
- Any remaining direct-boundary residue is removed.
- Focused finalize tests still pass.

## Subproblems
- none

## Results
- R325

## Latest Check
C346

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P336/children/P343/children/P345/README.md
- Ticket T332: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P336/children/P343/children/P345/tickets/T332.md
- Result R325: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P336/children/P343/children/P345/results/R325.md
- Check C346: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P336/children/P343/children/P345/checks/C346.md

## Follow-ups
- none
