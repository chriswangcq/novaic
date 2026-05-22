# P031: Gateway Production Cutover Preflight

Status: done
Parent: P030
Root: P000
Source Ticket: T027 (split)
Source Check: none
Package: problems/P000/children/P024/children/P025/children/P030/children/P031
Body: problems/P000/children/P024/children/P025/children/P030/children/P031/README.md
Ticket(s): T028

## Problem
Before switching production Gateway to Postgres, remote runtime, dependencies, secrets, source DB counts, target DB state, and migration mechanics must be verified without restarting Gateway or changing its runtime backend.

## Success Criteria
- Remote Gateway runtime path, process args, and health are captured.
- Remote venv/dependency readiness for `psycopg` is verified or prepared.
- Gateway Postgres DSN file path/permissions are prepared without exposing credentials.
- Source SQLite row counts for `users`, `refresh_tokens`, and `config` are captured.
- Target `novaic_gateway` readiness is verified.
- A migration command/script path is prepared and safe to run in execution.
- No production Gateway restart or backend switch happens in this preflight.

## Subproblems
- none

## Results
- R025

## Latest Check
C025

## Bodies
- Problem: problems/P000/children/P024/children/P025/children/P030/children/P031/README.md
- Ticket T028: problems/P000/children/P024/children/P025/children/P030/children/P031/tickets/T028.md
- Result R025: problems/P000/children/P024/children/P025/children/P030/children/P031/results/R025.md
- Check C025: problems/P000/children/P024/children/P025/children/P030/children/P031/checks/C025.md

## Follow-ups
- none
