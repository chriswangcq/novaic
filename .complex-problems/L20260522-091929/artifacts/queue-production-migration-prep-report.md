# Queue Production Migration Preparation Report

## Summary

- Status: success
- Cutover runtime: `/opt/novaic/services/novaic-agent-runtime-pg`
- Runtime commit: `6c464b8b0796b3f1b31729d4d36afe81778a0fd0`
- Runtime status after preparation: clean, excluding the intentional `.venv` symlink
- Cutover venv: `/opt/novaic/services/novaic-agent-runtime-pg/.venv-cutover`
- Target database: `novaic_queue`
- Source SQLite backup: `/opt/novaic/backups/queue-cutover/20260523T011125Z/queue.db`

## Target Safety

- Pre-clear known Queue rows: 0
- Post-prepare known Queue rows: 0
- Target pg_dump backup: `/opt/novaic/backups/queue-cutover/20260523T011125Z/pre-migration-novaic_queue.sql`
- Target backup size: 1065 bytes
- Target backup SHA256: `e3140a50f927632174e27db721adce3692979f1202d3e7cdbb63f896b227afa3`

## Dry Run

- Dry-run status: ready
- Dry-run errors: none
- Target clean: yes
- Table inspections: 16
- Remote dry-run report: `/opt/novaic/backups/queue-cutover/20260523T011125Z/queue-migration-dry-run-report.json`
- Local dry-run artifact: `.complex-problems/L20260522-091929/artifacts/queue-production-migration-dry-run-report.json`

## Notes

- The legacy production runtime at `/opt/novaic/services/novaic-agent-runtime` remains dirty and was not overwritten.
- A clean cutover runtime was created for the Postgres migration and later Queue restart work.
- The Queue Postgres DSN is stored on the server as a root-readable credential file and is redacted from artifacts.
