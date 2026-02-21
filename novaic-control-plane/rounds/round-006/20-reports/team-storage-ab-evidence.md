# Storage-A/B Round 006 Canonical Evidence

- executed_at_utc: 2026-02-21T02:12:03Z
- replay_script: `rounds/round-006/20-reports/storage_ab_round006_non_author_replay.sh`

## Repo anchors

| repo_url | branch | commit_sha |
|---|---|---|
| `file:///Users/wangchaoqun/novaic/novaic-storage-a` | `split/round-003-storage-a` | `b7cde077160cb3cfdeb03ba845e5a05cde1f82c7` |
| `file:///Users/wangchaoqun/novaic/novaic-storage-b` | `split/round-003-storage-b` | `634093753b61672c1539e53a9219222b15f1fb4d` |

## Step 1 — Storage-A smoke
- command: `cd novaic-storage-a && bash scripts/smoke_storage_a.sh`
- expected_marker: `STORAGE_A_SMOKE_OK=true`
- result: PASS
- artifact: `novaic-storage-a/artifacts/storage-a-smoke-latest.md`

## Step 2 — Storage-B restore validate
- command: `cd novaic-storage-b && bash scripts/validate_storage_b_restore.sh`
- expected_marker: `STORAGE_B_RESTORE_VALIDATE=PASS`
- result: PASS
- artifact: `novaic-storage-b/artifacts/storage-b-restore-validate-latest.md`

## Step 3 — Storage-B smoke
- command: `cd novaic-storage-b && bash scripts/smoke_storage_b.sh`
- expected_marker: `STORAGE_B_SMOKE_OK=true`
- result: PASS
- artifact: `novaic-storage-b/artifacts/storage-b-smoke-latest.md`

## Step 4 — Failure-injection cross-repo retry chain
- command: `cd novaic-storage-b && bash scripts/failure_injection_cross_repo_retry.sh`
- expected_marker: `STORAGE_AB_RETRY_INJECTION=PASS`, `RETRY_ATTEMPT_LOG=PASS`
- result: PASS
- artifact: `novaic-storage-b/artifacts/storage-ab-failure-injection-retry-latest.md`

## Non-author replay
- command: `bash rounds/round-006/20-reports/storage_ab_round006_non_author_replay.sh`
- expected_marker: `STORAGE_AB_ROUND006_REPLAY=PASS`
- result: PASS
