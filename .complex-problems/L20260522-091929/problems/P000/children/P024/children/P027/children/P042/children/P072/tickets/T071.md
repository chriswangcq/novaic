# Restart Business Services After Entangled Postgres Cutover

## Problem Definition

Business API and Business subscriber were intentionally stopped during the Entangled cutover window and remain stopped. Entangled is now Postgres-backed and ready, so Business services must be restarted against `http://127.0.0.1:19900` and verified.

## Proposed Solution

Use the restart commands recorded in the P063 backup/freeze report to start Business API and Business subscriber with the production venv and service paths. Write logs/PID files under `/opt/novaic`, wait for Business API health, confirm subscriber process is running, verify Entangled remains ready, verify no `entangled.db*` files are recreated or held, and inspect recent logs for schema/secret errors without printing raw secrets.

## Acceptance Criteria

- Business API process is running on `127.0.0.1:19998`.
- Business `/health` returns HTTP 200.
- Business subscriber process is running.
- Both processes use `--entangled-url http://127.0.0.1:19900`.
- Entangled remains `/v1/ready` HTTP 200 with 22 entities after restart.
- `/opt/novaic/data/entangled.db*` remains absent and unheld.
- Recent Business/Entangled logs show no schema registration or raw-secret leak errors.
- A redacted restart verification report is recorded.

## Verification Plan

Run remote process starts if no existing Business processes are present, then use `ss`, `pgrep`, `curl`, `find`, `lsof`, and sanitized log-tail checks. Store a report under the cutover archive and pull it into local ledger artifacts.

## Risks

- Subscriber may depend on queue-service availability and should be verified by process/log status, not only spawn success.
- Business startup may push schemas again; Entangled should remain ready and not recreate SQLite files.

## Assumptions

- Restart commands in the P063 freeze report are still correct.
- Queue service and Gateway are already running on their production loopback ports.
- Entangled PG runtime is the current state owner and should stay on port `19900`.
