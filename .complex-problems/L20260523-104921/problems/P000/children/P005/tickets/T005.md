# P005 Ticket

Update residue guards, focused tests, and ledger evidence so the Postgres-only service DB shape stays enforceable.

Problem definition:
- Manual cleanup is not enough; future generated code could reintroduce SQLite fallback names, flags, or file DB paths unless active runtime paths are guarded.
- Existing residue guards must be executable directly in CI.

Proposed solution:
- Add a service-side SQLite residue guard over active service/runtime/config paths.
- Make the guard runnable as a plain Python CI step and keep pytest compatibility.
- Fix any stale active-path residue revealed by the guard.
- Record verification evidence in the ledger.

Acceptance criteria:
- The guard fails on active service code containing SQLite/fallback tokens such as `sqlite3`, `--db-backend`, `queue.db`, `device.db`, `operational.sqlite3`, `GATEWAY_DB_FILE`, or `db_path`.
- CI runs the guard.
- Current guard execution passes.
- The final ledger evidence includes the cleanup and verification commands.

Verification plan:
- Run `python3 scripts/ci/test_no_legacy_file_hot_paths.py`.
- Run `pytest -q scripts/ci/test_no_legacy_file_hot_paths.py`.
- Run the service-side residue `rg` scan across active runtime/config paths.
