# Archive Queue SQLite Active Path Result

## Summary

The old active Queue SQLite path on the API host was moved out of `/opt/novaic/data` into the cutover backup archive after the Queue stack was already running and smoke-tested on Postgres. The live SQLite path and WAL/SHM sidecars are absent, Queue health and readiness still pass against Postgres, and the cleanup evidence was copied into local ledger artifacts.

## Done

- Verified no process held `/opt/novaic/data/queue.db` before cleanup.
- Archived `/opt/novaic/data/queue.db`, `queue.db-wal`, and `queue.db-shm` into `/opt/novaic/backups/queue-cutover/20260523T011125Z/archived-active-sqlite-20260523T021156Z/`.
- Recorded file sizes and hashes for the archived SQLite files.
- Verified the live SQLite path and sidecars no longer exist after archive.
- Verified Queue `/health` still reports Postgres and Queue `/ready` returns HTTP 200 after archive.
- Verified no process held `/opt/novaic/data/queue.db` after cleanup.
- Copied the archive report into the ledger artifact directory and scanned the JSON/Markdown report for credential patterns.

## Verification

- `queue-sqlite-archive-report.md` records status `success`, health backend `postgres`, ready status `200`, and no SQLite holders before or after the archive.
- Archived `queue.db` size is `378683392` bytes with SHA256 `07a65534bfd932694202c0a8f06df0426a1777b1bca5800d31c0f9d44df44153`, matching the earlier freeze backup hash.
- Redaction scan over `queue-sqlite-archive-report.json` and `queue-sqlite-archive-report.md` returned no matches for DSNs, passwords, tokens, private keys, or the Postgres secret path.

## Known Gaps

- This ticket only archived the Queue SQLite active path. Other services' legacy SQLite paths and broader Postgres cleanup remain governed by the parent migration ledger items.
- Rollback now requires intentionally restoring the archived SQLite file instead of relying on accidental live-path fallback.

## Artifacts

- `.complex-problems/L20260522-091929/artifacts/queue-sqlite-archive-report.json`
- `.complex-problems/L20260522-091929/artifacts/queue-sqlite-archive-report.md`
- Remote report: `/opt/novaic/backups/queue-cutover/20260523T011125Z/queue-sqlite-archive-report.json`
- Remote archive directory: `/opt/novaic/backups/queue-cutover/20260523T011125Z/archived-active-sqlite-20260523T021156Z/`
