# P004: Verify published server health and close deployment evidence

Status: todo
Parent: P000
Root: P000
Source Ticket: T000 (split)
Source Check: none
Package: problems/P000/children/P004
Body: problems/P000/children/P004/README.md
Ticket(s): none

## Problem
A controller success is not enough without confirming the server endpoints are live after deployment. The deployment needs a final health/smoke pass and a concise evidence package.

## Success Criteria
- API/backend server health or smoke endpoints pass for the deployed namespace.
- Registry/service state is consistent enough to prove server-side services came up.
- Final evidence includes commit SHAs, controller run ID, namespace, health URLs, and residual risks.
- Ledger validates/renders complete after closure.

## Subproblems
- none

## Results
- none

## Latest Check
none

## Bodies
- Problem: problems/P000/children/P004/README.md

## Follow-ups
- none
