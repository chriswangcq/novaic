# Round 004 Storage-A/B Repo Governance Snapshot

## Repo configuration snapshot

| repo_url | default_branch | ruleset_or_protection_id | required_checks | permission_model | codeowners |
|---|---|---|---|---|---|
| `file:///Users/wangchaoqun/novaic/novaic-storage-a` | `split/round-003-storage-a` | `LOCAL_ONLY_NO_GITHUB_RULESET` | `storage-a-smoke` | `local-maintainer-only` | `N/A (local split candidate)` |
| `file:///Users/wangchaoqun/novaic/novaic-storage-b` | `split/round-003-storage-b` | `LOCAL_ONLY_NO_GITHUB_RULESET` | `storage-b-restore-validate`, `storage-b-smoke`, `cross-repo-chain-round004` | `local-maintainer-only` | `N/A (local split candidate)` |

## Split commit references

- `novaic-storage-a`: `b7cde077160cb3cfdeb03ba845e5a05cde1f82c7`
- `novaic-storage-b`: `221b177d7d45c473101426932c85b60ac94fce65`

## Migrated paths (Round 004 increment)

- `novaic-backend/scripts/storage_ab_backup.sh` -> `novaic-storage-a/scripts/storage_a_backup.sh`
- `novaic-backend/scripts/storage_ab_restore.sh` -> `novaic-storage-a/scripts/storage_a_restore.sh`
- `novaic-backend/scripts/storage_ab_backup.sh` -> `novaic-storage-b/scripts/storage_b_backup.sh` (DB domain extraction)
- `novaic-backend/scripts/storage_ab_restore.sh` -> `novaic-storage-b/scripts/storage_b_restore.sh` (DB domain extraction)
- `novaic-backend/scripts/storage_ab_validate_restore.sh` -> `novaic-storage-b/scripts/validate_storage_b_restore.sh` (Storage-B specific validate replay)
- `novaic-backend/tool_result_service/clients.py` monorepo import -> `novaic-storage-b/tool_result_service/clients.py` direct HTTP API client
