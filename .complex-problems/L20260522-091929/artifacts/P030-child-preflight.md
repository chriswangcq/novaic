# Gateway Production Cutover Preflight

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
