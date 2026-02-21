# Storage-A/B Round 007 Non-Author Replay Evidence

- executed_at_utc: 2026-02-21T02:24:29Z
- replay_script: `rounds/round-006/20-reports/storage_ab_round006_non_author_replay.sh`
- workspace_root: `${WORKSPACE_ROOT:-$HOME/novaic}`

## Repo anchors (canonical form)

| canonical_repo_url | branch | commit_sha |
|---|---|---|
| `file:///Users/wangchaoqun/novaic/novaic-storage-a` | `split/round-003-storage-a` | `b7cde077160cb3cfdeb03ba845e5a05cde1f82c7` |
| `file:///Users/wangchaoqun/novaic/novaic-storage-b` | `split/round-003-storage-b` | `634093753b61672c1539e53a9219222b15f1fb4d` |

## Step-by-step replay results

| step | command | expected_marker | result |
|---|---|---|---|
| 1 | `cd novaic-storage-a && bash scripts/smoke_storage_a.sh` | `STORAGE_A_SMOKE_OK=true` | PASS |
| 2 | `cd novaic-storage-b && bash scripts/validate_storage_b_restore.sh` | `STORAGE_B_RESTORE_VALIDATE=PASS` | PASS |
| 3 | `cd novaic-storage-b && bash scripts/smoke_storage_b.sh` | `STORAGE_B_SMOKE_OK=true` | PASS |
| 4 | `cd novaic-storage-b && bash scripts/failure_injection_cross_repo_retry.sh` | `STORAGE_AB_RETRY_INJECTION=PASS`, `RETRY_ATTEMPT_LOG=PASS` | PASS |

## Final marker

```
STORAGE_AB_ROUND006_REPLAY=PASS
```
