# Round 002 Storage-A Repo Candidate (Storage-A/B Team)

## Candidate repo and owner

| candidate_repo | owner_team | extraction_source_paths | runtime_entrypoints |
|---|---|---|---|
| `novaic-storage-a` | `Storage-A/B Team` | `novaic-backend/file_service/**` | `python -m file_service.main` |

## Physical split extraction boundary

1. Move file object storage implementation under `file_service` into `novaic-storage-a`.
2. Keep shared contract assets under `contracts/**` and consume as versioned dependency.
3. Export only API interfaces (health, write/read/info) for gateway/runtime/tools consumers.
4. Preserve smoke replay compatibility through `novaic-backend/scripts/storage_ab_smoke.sh`.

## Ready-to-run baseline markers

- `FILE_SERVICE_HEALTH=PASS` (from smoke evidence)
- `FILE_WRITE_READ=PASS` (from smoke evidence)
