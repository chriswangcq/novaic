# P097: Port Session Rebuild And Read Models To Postgres

Status: done
Parent: P082
Root: P000
Source Ticket: none (none)
Source Check: C095
Package: problems/P000/children/P024/children/P028/children/P074/children/P082/children/P097
Body: problems/P000/children/P024/children/P028/children/P074/children/P082/children/P097/README.md
Ticket(s): T093

## Problem
`P082` still needs explicit coverage for session rebuild and read-model behavior under Postgres. Startup rebuild currently needs deterministic ordering, backend-safe SQL, and a clear serialization rule so it cannot race live dispatch or reconstruct active sessions from SQLite-specific assumptions.

## Success Criteria
- Inspect `queue_service/session_rebuild.py` and related session read-model methods for SQLite-only SQL, implicit ordering, or startup race assumptions.
- Add Postgres-safe ordering and locking/advisory-lock helpers where needed for session rebuild.
- Ensure rebuild marks stale active session state and reconstructs active state from running/launched sagas with deterministic ordering.
- Add focused tests for Postgres rebuild/read-model SQL shape or deterministic behavior.
- Run the new tests with existing session rebuild, session state SSOT, queue Postgres boundary, and session locking regressions.

## Subproblems
- none

## Results
- R090

## Latest Check
C096

## Bodies
- Problem: problems/P000/children/P024/children/P028/children/P074/children/P082/children/P097/README.md
- Ticket T093: problems/P000/children/P024/children/P028/children/P074/children/P082/children/P097/tickets/T093.md
- Result R090: problems/P000/children/P024/children/P028/children/P074/children/P082/children/P097/results/R090.md
- Check C096: problems/P000/children/P024/children/P028/children/P074/children/P082/children/P097/checks/C096.md

## Follow-ups
- none
