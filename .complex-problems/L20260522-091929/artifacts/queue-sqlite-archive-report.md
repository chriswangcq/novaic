# Queue SQLite Archive Report

## Summary

- Status: success
- Archive directory: `/opt/novaic/backups/queue-cutover/20260523T011125Z/archived-active-sqlite-20260523T021156Z`
- Live `/opt/novaic/data/queue.db`: removed
- Live WAL/SHM sidecars: removed
- Queue health backend after archive: postgres
- Queue ready after archive: 200
- SQLite holders before archive: none
- SQLite holders after archive: none

## Archived Files

- `queue.db`: 378683392 bytes, SHA256 `07a65534bfd932694202c0a8f06df0426a1777b1bca5800d31c0f9d44df44153`
- `queue.db-wal`: 0 bytes, SHA256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- `queue.db-shm`: 32768 bytes, SHA256 `fd4c9fda9cd3f9ae7c962b0ddf37232294d55580e1aa165aa06129b8549389eb`

## Artifacts

- Remote archive report: `/opt/novaic/backups/queue-cutover/20260523T011125Z/queue-sqlite-archive-report.json`
- Local archive report: `.complex-problems/L20260522-091929/artifacts/queue-sqlite-archive-report.json`
- Remote archive README: `/opt/novaic/backups/queue-cutover/20260523T011125Z/archived-active-sqlite-20260523T021156Z/README.md`
