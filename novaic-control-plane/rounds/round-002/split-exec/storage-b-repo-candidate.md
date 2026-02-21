# Round 002 Storage-B Repo Candidate (Storage-A/B Team)

## Candidate repo and owner

| candidate_repo | owner_team | extraction_source_paths | runtime_entrypoints |
|---|---|---|---|
| `novaic-storage-b` | `Storage-A/B Team` | `novaic-backend/tool_result_service/**` | `python -m tool_result_service.main` |

## Physical split extraction boundary

1. Move tool result persistence/query service under `tool_result_service` into `novaic-storage-b`.
2. Keep contract definitions versioned in shared location (`contracts/openapi/**`, `contracts/schema/**`).
3. Expose result create/read API boundary only; prohibit cross-repo internal module imports.
4. Preserve replay compatibility through `storage_ab_validate_restore.sh` and `storage_ab_smoke.sh`.

## Ready-to-run baseline markers

- `TOOL_RESULT_SERVICE_HEALTH=PASS` (from smoke evidence)
- `TOOL_RESULT_WRITE_READ=PASS` (from smoke evidence)
- `RESTORE_OK=true` (from restore replay)
