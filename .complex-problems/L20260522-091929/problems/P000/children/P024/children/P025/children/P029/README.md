# Implement Gateway Postgres Storage Path

## Problem

Gateway needs a production Postgres storage path for `users`, `refresh_tokens`, and `config` before any production cutover. The implementation must preserve current auth/config behavior and avoid keeping production SQLite fallback logic.

## Success Criteria

- Gateway can initialize and use Postgres storage for `users`, `refresh_tokens`, and `config`.
- Postgres DDL is explicit and does not recreate retired zero-row Gateway tables.
- Current Gateway auth/config APIs keep their expected row shapes and error behavior.
- Focused local tests cover the Postgres-backed storage path or an explicit adapter contract.
- Production SQLite fallback is not part of the final runtime path.
- No production data is mutated by this implementation-only problem.
