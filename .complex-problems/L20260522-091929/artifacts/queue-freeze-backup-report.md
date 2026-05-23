# Queue Freeze And Final SQLite Backup Report

## Summary

- Status: success
- Generated at: 2026-05-23T01:11:25Z
- Source SQLite: `/opt/novaic/data/queue.db`
- Backup directory: `/opt/novaic/backups/queue-cutover/20260523T011125Z`
- Backup SQLite: `/opt/novaic/backups/queue-cutover/20260523T011125Z/queue.db`
- Backup size: 378683392 bytes
- Source mtime: 2026-05-20T14:13:52.513230Z

## Freeze Evidence

- Pre-freeze target process count: 13
- Freeze action order:
  - gateway queue ingress
  - business subscriber
  - queue scheduler
  - queue health
  - task workers
  - saga workers
  - session outbox worker
  - saga outbox worker
  - queue service
- Post-freeze target process count: 0
- Post-freeze SQLite holder PIDs: none
- Post-backup SQLite holder PIDs: none

## Backup Evidence

- Source SHA256: `07a65534bfd932694202c0a8f06df0426a1777b1bca5800d31c0f9d44df44153`
- Backup SHA256: `07a65534bfd932694202c0a8f06df0426a1777b1bca5800d31c0f9d44df44153`
- SHA256 match: yes
- SQLite integrity_check: ok
- Remote report: `/opt/novaic/backups/queue-cutover/20260523T011125Z/freeze-backup-report.json`
- Local JSON artifact: `.complex-problems/L20260522-091929/artifacts/queue-freeze-backup-report.json`

## Notes

- No force kill was required.
- The production Queue runtime is intentionally frozen after this step so the next ledger action can migrate a stable SQLite snapshot into production Postgres.
