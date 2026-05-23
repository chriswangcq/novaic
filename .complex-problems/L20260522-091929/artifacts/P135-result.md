# Queue Postgres Cleanup Notes Update Result

## Summary

Updated the API host Queue cleanup documentation so the central SQLite classification no longer describes `queue.db` as active. Queue is now documented as Postgres-backed, with the archived SQLite files marked rollback-only and retained through a defined stabilization window.

## Done

- Updated `/opt/novaic/data/SQLITE_STATE_CLASSIFICATION.md` on `api.gradievo.com` so `/opt/novaic/data/queue.db` is `archived/rollback-only non-current SQLite snapshot`.
- Added a Queue Postgres cutover addendum to the central classification note naming Postgres database `novaic_queue` as the current source of truth.
- Created `/opt/novaic/backups/queue-cutover/20260523T011125Z/QUEUE_POSTGRES_CUTOVER.md` with cutover evidence, backup checksum, archive location, rollback expectation, and retention/retirement policy.
- Saved a remote verification report at `/opt/novaic/backups/queue-cutover/20260523T011125Z/queue-cleanup-notes-update-report.json`.
- Copied sanitized local artifacts into `.complex-problems/L20260522-091929/artifacts/`.

## Verification

- Remote report `ok` is `true`.
- Remote checks confirmed the central classification exists, the rollback note exists, the Queue row is archived, the old `defer-high-risk active-state-owner` Queue classification is gone, Postgres `novaic_queue` is named as source of truth, and the rollback note contains archive path, checksum, restore expectation, and retention through `2026-06-22 Asia/Shanghai`.
- Remote grep confirmed the Queue classification row and Queue Postgres cutover addendum in `/opt/novaic/data/SQLITE_STATE_CLASSIFICATION.md`.
- Remote grep confirmed rollback and retention sections in `/opt/novaic/backups/queue-cutover/20260523T011125Z/QUEUE_POSTGRES_CUTOVER.md`.
- Local sanitized artifacts were scanned for `postgres://`, `postgresql://`, password/passwd, secret, token, API-key patterns, private-key markers, and raw `/opt/novaic/postgres/secrets` paths; the final scan returned no matches.

## Known Gaps

- The central note still records other service classifications, including remaining non-Queue SQLite owners such as Gateway and Cortex; those are outside this follow-up and remain governed by the parent migration ledger.
- Remote operational notes intentionally include credential-file paths for operators, but local ledger copies are sanitized before commit.

## Artifacts

- `.complex-problems/L20260522-091929/artifacts/queue-cleanup-notes-update-report.json`
- `.complex-problems/L20260522-091929/artifacts/SQLITE_STATE_CLASSIFICATION.after-queue-redacted.md`
- `.complex-problems/L20260522-091929/artifacts/QUEUE_POSTGRES_CUTOVER.redacted.md`
- Remote central note: `/opt/novaic/data/SQLITE_STATE_CLASSIFICATION.md`
- Remote rollback note: `/opt/novaic/backups/queue-cutover/20260523T011125Z/QUEUE_POSTGRES_CUTOVER.md`
