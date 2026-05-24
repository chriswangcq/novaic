# P000: Enroll prod into release-controller immutable promote and rollback pointers

Status: done
Parent: none
Root: P000
Source Ticket: none (none)
Source Check: none
Package: problems/P000
Body: problems/P000/README.md
Ticket(s): T000

## Problem
Prod is containerized and healthy, but release-controller state only tracks staging. Prod must become a first-class immutable release namespace: promotion should deploy immutable refs, current/previous pointers should exist, and rollback should be planned from release-controller state rather than from mutable Docker tags.

## Success Criteria
- Prod has a release-controller `current_releases` pointer with namespace `prod` and immutable API/Factory image refs.
- Prod has a `previous_releases` pointer so `/v1/rollbacks/prod` has a real target immediately.
- The current prod deployment is promoted from the staging-verified commit `4e52e7ea8e2f0722be550ce36a19ea8d8cae8a21` using immutable refs.
- Prod API and Factory containers run image refs that match the release-controller prod current pointer.
- Prod health checks pass locally and public prod ingress behavior is understood.
- A dry-run rollback for prod succeeds and points to the previous immutable prod pointer without mutating current prod.
- Ledger validation/rendering/status pass.

## Subproblems
- none

## Results
- R000

## Latest Check
C000

## Bodies
- Problem: problems/P000/README.md
- Ticket T000: problems/P000/tickets/T000.md
- Result R000: problems/P000/results/R000.md
- Check C000: problems/P000/checks/C000.md

## Follow-ups
- none
