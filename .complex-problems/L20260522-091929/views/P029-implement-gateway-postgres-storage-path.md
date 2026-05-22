# P029: Implement Gateway Postgres Storage Path

Status: done
Parent: P025
Root: P000
Source Ticket: T025 (split)
Source Check: none
Package: problems/P000/children/P024/children/P025/children/P029
Body: problems/P000/children/P024/children/P025/children/P029/README.md
Ticket(s): T026

## Problem
Gateway needs a production Postgres storage path for `users`, `refresh_tokens`, and `config` before any production cutover. The implementation must preserve current auth/config behavior and avoid keeping production SQLite fallback logic.

## Success Criteria
- Gateway can initialize and use Postgres storage for `users`, `refresh_tokens`, and `config`.
- Postgres DDL is explicit and does not recreate retired zero-row Gateway tables.
- Current Gateway auth/config APIs keep their expected row shapes and error behavior.
- Focused local tests cover the Postgres-backed storage path or an explicit adapter contract.
- Production SQLite fallback is not part of the final runtime path.
- No production data is mutated by this implementation-only problem.

## Subproblems
- none

## Results
- R024

## Latest Check
C024

## Bodies
- Problem: problems/P000/children/P024/children/P025/children/P029/README.md
- Ticket T026: problems/P000/children/P024/children/P025/children/P029/tickets/T026.md
- Result R024: problems/P000/children/P024/children/P025/children/P029/results/R024.md
- Check C024: problems/P000/children/P024/children/P025/children/P029/checks/C024.md

## Follow-ups
- none
