# P146: write_step payload_ref mirroring audit

Status: done
Parent: P142
Root: P000
Source Ticket: T129 (split)
Source Check: none
Package: problems/P000/children/P003/children/P126/children/P134/children/P142/children/P146
Body: problems/P000/children/P003/children/P126/children/P134/children/P142/children/P146/README.md
Ticket(s): T131

## Problem
`write_step` must externalize raw payload data through the workspace payload store and mirror the actual `payload_ref` back into the stored observation. If this fails, step JSON can point at stale refs, miss full-output recovery, or retain large payload data inline.

This child belongs under `P142` because payload pointer integrity is the core boundary between compact step records and full reconstructable tool output.

## Success Criteria
- Source pointers map where `write_step` detects observation payloads and calls payload storage.
- Evidence proves raw payload writes require or produce a `payload_ref`.
- Evidence proves the stored step observation contains the actual persisted `payload_ref`.
- Tests cover local payload and external blob-backed payload behavior where relevant.

## Subproblems
- none

## Results
- R126

## Latest Check
C140

## Bodies
- Problem: problems/P000/children/P003/children/P126/children/P134/children/P142/children/P146/README.md
- Ticket T131: problems/P000/children/P003/children/P126/children/P134/children/P142/children/P146/tickets/T131.md
- Result R126: problems/P000/children/P003/children/P126/children/P134/children/P142/children/P146/results/R126.md
- Check C140: problems/P000/children/P003/children/P126/children/P134/children/P142/children/P146/checks/C140.md

## Follow-ups
- none
