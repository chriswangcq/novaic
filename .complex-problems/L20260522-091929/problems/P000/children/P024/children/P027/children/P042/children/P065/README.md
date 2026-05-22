# Restart Production Entangled In Postgres Mode

## Problem

After final migration succeeds, production Entangled must be restarted on the existing production port using Postgres and file-based secrets. This belongs under `P042` because the cutover is not complete until the production runtime serves from Postgres instead of SQLite.

## Success Criteria

- Existing SQLite-mode Entangled process is stopped in the controlled cutover window.
- Entangled starts on `127.0.0.1:19900` with `--db-backend postgres`, `--postgres-dsn-file`, and `--service-token-file`.
- Process args do not contain raw DSN or raw service-token values.
- Health/readiness return success after restart.
- No process holds `/opt/novaic/data/entangled.db*` after restart.
- A rollback command/path is recorded if the Postgres-mode runtime fails.
