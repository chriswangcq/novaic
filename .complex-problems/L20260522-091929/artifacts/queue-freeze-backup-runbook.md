# Queue Freeze And Final SQLite Backup Runbook

Generated: 2026-05-22 17:46 UTC / 2026-05-23 01:46 Asia/Shanghai

## Purpose

Freeze production Queue writers, take the final rollback SQLite backup, and prove the active Queue file is no longer held before migration. This runbook is preparation only; executing it belongs to P129.

## Current Evidence Source

- Preflight report: `.complex-problems/L20260522-091929/artifacts/queue-production-preflight-inventory.md`
- Inventory JSON: `.complex-problems/L20260522-091929/artifacts/queue-production-preflight-inventory.json`
- Active Queue file: `/opt/novaic/data/queue.db`
- Production Queue URL before cutover: `http://127.0.0.1:19997`
- Production target database exists: `novaic_queue` in `novaic-postgres`

## Stop/Frozen Target Order

Refresh PIDs immediately before execution; do not trust the snapshot blindly.

1. Stop Queue ingress and schedulers:
   - gateway using Queue URL `19997`
   - business subscriber using Queue URL `19997`
   - Queue scheduler
   - Queue health worker
2. Stop Queue workers:
   - task workers, pools `control` and `execution`
   - saga workers
   - session outbox worker
   - saga outbox worker
3. Stop Queue Service last:
   - `main_novaic.py queue-service --port 19997 --data-dir /opt/novaic/data`

## Pre-Execution Checklist

Run on `api.gradievo.com`:

```bash
set -euo pipefail
date -u
ps -eo pid,ppid,user,lstart,cmd | egrep 'main_novaic.py (queue-service|task-worker|saga-worker|session-outbox-worker|saga-outbox-worker|health|scheduler)|main_subscriber.py|main_gateway.py'
lsof /opt/novaic/data/queue.db || true
curl -fsS http://127.0.0.1:19997/health
curl -fsS http://127.0.0.1:19997/ready
stat /opt/novaic/data/queue.db
```

Abort if:

- `queue.db` is missing.
- production Queue health/readiness is already failing before freeze.
- an unexpected writer process appears that is not in the stop plan.
- there is no approved freeze window.

## Freeze Commands

Use refreshed PIDs where possible. These pattern commands are intentionally specific to production Queue roles:

```bash
set -euo pipefail

# 1. Freeze Queue ingress and scheduled producers.
pkill -TERM -f 'main_gateway.py .*--queue-service-url http://127.0.0.1:19997' || true
pkill -TERM -f 'main_subscriber.py .*--queue-service-url http://127.0.0.1:19997' || true
pkill -TERM -f 'main_novaic.py scheduler .*--queue-service-url http://127.0.0.1:19997' || true
pkill -TERM -f 'main_novaic.py health .*--queue-service-url http://127.0.0.1:19997' || true

# 2. Stop Queue consumers and outbox workers.
pkill -TERM -f 'main_novaic.py task-worker .*--queue-service-url http://127.0.0.1:19997' || true
pkill -TERM -f 'main_novaic.py saga-worker .*--queue-service-url http://127.0.0.1:19997' || true
pkill -TERM -f 'main_novaic.py session-outbox-worker --data-dir /opt/novaic/data' || true
pkill -TERM -f 'main_novaic.py saga-outbox-worker --data-dir /opt/novaic/data' || true

# 3. Stop Queue Service last.
pkill -TERM -f 'main_novaic.py queue-service --host 127.0.0.1 --port 19997 --data-dir /opt/novaic/data' || true

sleep 5
```

If any process survives, inspect it before escalating:

```bash
ps -eo pid,ppid,user,lstart,cmd | egrep 'main_novaic.py (queue-service|task-worker|saga-worker|session-outbox-worker|saga-outbox-worker|health|scheduler)|main_subscriber.py|main_gateway.py' || true
lsof /opt/novaic/data/queue.db || true
```

Only use `kill -KILL` for a specific reviewed PID if it still blocks the SQLite file and graceful termination has failed.

## Backup Commands

```bash
set -euo pipefail
TS=$(date -u +%Y%m%dT%H%M%SZ)
BACKUP_DIR=/opt/novaic/backups/queue-cutover/$TS
mkdir -p "$BACKUP_DIR"
chmod 700 /opt/novaic/backups/queue-cutover "$BACKUP_DIR"

cp -p /opt/novaic/data/queue.db "$BACKUP_DIR/queue.db"
sha256sum /opt/novaic/data/queue.db "$BACKUP_DIR/queue.db" > "$BACKUP_DIR/queue-db.sha256"
stat /opt/novaic/data/queue.db "$BACKUP_DIR/queue.db" > "$BACKUP_DIR/queue-db.stat"
sqlite3 "$BACKUP_DIR/queue.db" 'PRAGMA integrity_check;' > "$BACKUP_DIR/queue-db.integrity.txt"
```

Expected:

- Checksums for source and backup match.
- `PRAGMA integrity_check` output is `ok`.
- Backup file size matches source file size.

## Post-Backup Holder Check

```bash
lsof /opt/novaic/data/queue.db || true
ps -eo pid,ppid,user,lstart,cmd | egrep 'main_novaic.py (queue-service|task-worker|saga-worker|session-outbox-worker|saga-outbox-worker|health|scheduler)|main_subscriber.py|main_gateway.py' || true
```

Block migration if:

- Any Queue writer/worker still holds `/opt/novaic/data/queue.db`.
- Queue Service has restarted in sqlite mode.
- Backup checksum/integrity check failed.

## Rollback Notes

Before migration, rollback is simply to restart the original sqlite-mode services using `/opt/novaic/data/queue.db`. After migration starts, rollback requires stopping Postgres-mode Queue services, restoring the timestamped backup over `/opt/novaic/data/queue.db`, and restarting the original services.

Do not delete or overwrite the timestamped backup during the cutover window.

## Artifact Expectations For P129

P129 should save:

- refreshed process inventory before freeze
- freeze command output
- backup directory path
- `queue-db.sha256`
- `queue-db.stat`
- `queue-db.integrity.txt`
- post-backup `lsof` and process checks
- go/no-go decision for migration
