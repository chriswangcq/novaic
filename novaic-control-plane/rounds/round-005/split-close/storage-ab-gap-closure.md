# Round 005 Storage-A/B Gap Closure

## Repo commit anchors

| repo_url | commit_sha |
|---|---|
| `file:///Users/wangchaoqun/novaic/novaic-storage-a` | `b7cde077160cb3cfdeb03ba845e5a05cde1f82c7` |
| `file:///Users/wangchaoqun/novaic/novaic-storage-b` | `634093753b61672c1539e53a9219222b15f1fb4d` |

## Gap closure code moves

- `novaic-backend/tool_result_service/resolver.py` -> `novaic-storage-b/tool_result_service/resolver.py`
  - Added retry policy (`STORAGE_B_RESOLVE_TIMEOUT_SECONDS`, `STORAGE_B_RESOLVE_MAX_RETRIES`, `STORAGE_B_RESOLVE_RETRY_DELAY_SECONDS`).
- New failure-injection replay entrypoint:
  - `novaic-storage-b/scripts/failure_injection_cross_repo_retry.sh`

## API-only integration proof

- Scope scan command:
  - `python - <<'PY' ... scan storage-a/storage-b for 'from common.' and 'import common.' ... PY`
- PASS marker:
  - `STORAGE_AB_API_ONLY_IMPORTS=PASS`

## Replay commands and markers

- `cd novaic-storage-a && bash scripts/smoke_storage_a.sh`
  - marker: `STORAGE_A_SMOKE_OK=true`
- `cd novaic-storage-b && bash scripts/validate_storage_b_restore.sh`
  - marker: `STORAGE_B_RESTORE_VALIDATE=PASS`
- `cd novaic-storage-b && bash scripts/smoke_storage_b.sh`
  - marker: `STORAGE_B_SMOKE_OK=true`
- `cd novaic-storage-b && bash scripts/failure_injection_cross_repo_retry.sh`
  - markers: `STORAGE_AB_RETRY_INJECTION=PASS`, `RETRY_ATTEMPT_LOG=PASS`
