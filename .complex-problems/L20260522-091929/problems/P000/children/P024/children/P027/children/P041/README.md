# Entangled production Postgres cutover preflight

## Problem

Before switching production Entangled to Postgres, capture fresh runtime, data, dependency, and rollback evidence, and confirm the production host can execute the cutover safely.

## Success Criteria

- Current Entangled health/readiness/runtime process state is captured.
- Fresh source SQLite counts, sync-version count/max, transition count/max ID, and representative table inventory are captured.
- `novaic_entangled` target connectivity and DSN secret permissions are verified without exposing secrets.
- Deployed Entangled code and migration tool are present and compile/import correctly on the production host.
- Current writers and file holders for `/opt/novaic/data/entangled.db*` are identified for the cutover plan.
- Rollback archive location is prepared before production execution.
- Entangled remains on SQLite after preflight; no production runtime switch occurs in this problem.
