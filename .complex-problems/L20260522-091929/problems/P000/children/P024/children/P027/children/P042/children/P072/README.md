# Restart Business Services After Entangled Postgres Cutover

## Problem

The Entangled SQLite-to-Postgres cutover is complete, but Business API and Business subscriber remain stopped from the writer-free cutover window. They must be restarted against the PG-mode Entangled runtime and verified before the production cutover is operationally complete.

## Success Criteria

- Business API is running on its production loopback port and points at `http://127.0.0.1:19900` for Entangled.
- Business subscriber is running with the production service paths/config.
- Business health/readiness or representative endpoint checks pass.
- Business schema push/startup does not reintroduce Entangled schema errors.
- Entangled remains health/ready HTTP 200 with 22 entities after Business restart.
- No process recreates or holds `/opt/novaic/data/entangled.db*`.
- Process/log inspection records no raw DSN/token/JWT values.
- A restart verification report is recorded in ledger artifacts.
