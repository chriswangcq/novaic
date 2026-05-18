# P502: Recovery stack diagnostics hardening

Status: done
Parent: P491
Root: P000
Source Ticket: T493 (split)
Source Check: none
Package: problems/P000/children/P004/children/P279/children/P482/children/P491/children/P502
Body: problems/P000/children/P004/children/P279/children/P482/children/P491/children/P502/README.md
Ticket(s): T495

## Problem
Suspected-dead and recovery archive paths should preserve explicit stack diagnostics or mark them unknown explicitly. They must not silently lose `remaining_stack` and then fabricate an empty stack in a way that hides wake corruption.

## Success Criteria
- Suspected-dead payloads preserve recovery stack diagnostics when available.
- Recovery archive effect construction no longer silently turns missing diagnostics into a known empty stack.
- Any unavoidable unknown-stack case is explicit in payload/result semantics.
- Focused tests cover both preserved stack diagnostics and unknown-stack behavior.

## Subproblems
- none

## Results
- R490

## Latest Check
C519

## Bodies
- Problem: problems/P000/children/P004/children/P279/children/P482/children/P491/children/P502/README.md
- Ticket T495: problems/P000/children/P004/children/P279/children/P482/children/P491/children/P502/tickets/T495.md
- Result R490: problems/P000/children/P004/children/P279/children/P482/children/P491/children/P502/results/R490.md
- Check C519: problems/P000/children/P004/children/P279/children/P482/children/P491/children/P502/checks/C519.md

## Follow-ups
- none
