# P005 Result

Updated residue guards and evidence for the service-side Postgres-only cleanup.

Concrete changes:
- `scripts/ci/test_no_legacy_file_hot_paths.py` now includes active service/runtime/config paths for Entangled server-python, Queue, Gateway, Device, Business, Common, Cortex, deploy/start scripts, and packaged config.
- Added `SERVICE_SQLITE_RESIDUE` guard tokens covering SQLite imports, SQLite backend flags, old DB file names, SQLite migration names, old DSN/config names, and misleading `db_path` naming.
- Made the guard runnable directly with `python3 scripts/ci/test_no_legacy_file_hot_paths.py` while keeping pytest compatibility.
- Wired the guard into `.github/workflows/lint.yml`.
- Cleaned stale packaged launcher references from `novaic-storage-a` to `novaic-blob-service`.

Verification:
- `python3 scripts/ci/test_no_legacy_file_hot_paths.py`
- `pytest -q scripts/ci/test_no_legacy_file_hot_paths.py`
- Service-side residue scan across current runtime/config paths returned no SQLite/fallback token hits.
