# Round 005 Report - Storage-A/B Team

## Task 1
- task: Remove residual internal imports and ensure Storage-A/B integration is API contract only.
- evidence:
  - command:
    - `python - <<'PY' ... scan storage-a/storage-b for 'from common.' and 'import common.' ... PY`
  - expected_marker:
    - `STORAGE_AB_API_ONLY_IMPORTS=PASS`
  - repo_url:
    - `file:///Users/wangchaoqun/novaic/novaic-storage-a`
    - `file:///Users/wangchaoqun/novaic/novaic-storage-b`
  - commit_sha:
    - `b7cde077160cb3cfdeb03ba845e5a05cde1f82c7`
    - `634093753b61672c1539e53a9219222b15f1fb4d`
  - migrated_paths:
    - `novaic-backend/tool_result_service/resolver.py -> novaic-storage-b/tool_result_service/resolver.py (API-only resolver path retained)`
    - `novaic-backend/tool_result_service/clients.py -> novaic-storage-b/tool_result_service/clients.py (API-only HTTP client retained)`
  - summary:
    - PASS; no residual `common.*` internal imports remain in Storage-A/B split repos.
  - artifact_path:
    - `novaic-control-plane/rounds/round-005/split-close/storage-ab-gap-closure.md`
- status: DONE

## Task 2
- task: Add failure-injection replay (timeout/retry) to cross-repo storage chain.
- evidence:
  - command:
    - `cd "/Users/wangchaoqun/novaic/novaic-storage-b" && bash scripts/failure_injection_cross_repo_retry.sh`
  - expected_marker:
    - `STORAGE_AB_RETRY_INJECTION=PASS`
    - `RETRY_ATTEMPT_LOG=PASS`
  - repo_url:
    - `file:///Users/wangchaoqun/novaic/novaic-storage-b`
  - commit_sha:
    - `634093753b61672c1539e53a9219222b15f1fb4d`
  - migrated_paths:
    - `novaic-backend/tool_result_service/resolver.py -> novaic-storage-b/tool_result_service/resolver.py (retry loop added)`
    - `new -> novaic-storage-b/scripts/failure_injection_cross_repo_retry.sh`
  - summary:
    - PASS; cross-repo failure injection now validates timeout/retry recovery and produces replayable markers.
  - artifact_path:
    - `novaic-storage-b/artifacts/storage-ab-failure-injection-retry-latest.md`
- status: DONE

## Task 3
- task: Run restore/smoke + cross-repo replay from split repo roots with PASS markers.
- evidence:
  - command:
    - `cd "/Users/wangchaoqun/novaic/novaic-storage-a" && bash scripts/smoke_storage_a.sh`
  - expected_marker:
    - `STORAGE_A_SMOKE_OK=true`
  - repo_url:
    - `file:///Users/wangchaoqun/novaic/novaic-storage-a`
  - commit_sha:
    - `b7cde077160cb3cfdeb03ba845e5a05cde1f82c7`
  - migrated_paths:
    - `novaic-backend/file_service/** -> novaic-storage-a/file_service/**`
  - summary:
    - PASS; Storage-A split root startup/health/read-write smoke succeeded.
  - artifact_path:
    - `novaic-storage-a/artifacts/storage-a-smoke-latest.md`
- evidence:
  - command:
    - `cd "/Users/wangchaoqun/novaic/novaic-storage-b" && bash scripts/validate_storage_b_restore.sh && bash scripts/smoke_storage_b.sh`
  - expected_marker:
    - `STORAGE_B_RESTORE_VALIDATE=PASS`
    - `STORAGE_B_SMOKE_OK=true`
  - repo_url:
    - `file:///Users/wangchaoqun/novaic/novaic-storage-b`
  - commit_sha:
    - `634093753b61672c1539e53a9219222b15f1fb4d`
  - migrated_paths:
    - `novaic-backend/scripts/storage_ab_validate_restore.sh -> novaic-storage-b/scripts/validate_storage_b_restore.sh`
    - `novaic-backend/tool_result_service/** -> novaic-storage-b/tool_result_service/**`
  - summary:
    - PASS; Storage-B split root restore validation and smoke replay succeeded.
  - artifact_path:
    - `novaic-storage-b/artifacts/storage-b-restore-validate-latest.md`
    - `novaic-storage-b/artifacts/storage-b-smoke-latest.md`
- evidence:
  - command:
    - `cd "/Users/wangchaoqun/novaic/novaic-storage-b" && bash scripts/failure_injection_cross_repo_retry.sh`
  - expected_marker:
    - `STORAGE_AB_RETRY_INJECTION=PASS`
  - repo_url:
    - `file:///Users/wangchaoqun/novaic/novaic-storage-b`
    - `file:///Users/wangchaoqun/novaic/novaic-storage-a`
  - commit_sha:
    - `634093753b61672c1539e53a9219222b15f1fb4d`
    - `b7cde077160cb3cfdeb03ba845e5a05cde1f82c7`
  - migrated_paths:
    - `novaic-storage-b/tool_result_service/resolver.py -> API call to novaic-storage-a file endpoint with retry`
  - summary:
    - PASS; split-root cross-repo replay succeeded under failure-injection conditions.
  - artifact_path:
    - `novaic-storage-b/artifacts/storage-ab-failure-injection-retry-latest.md`
- status: DONE

## Decision Needed (optional)
- issue:
- options:
- recommendation:
- impact:
- owner:
- target_round:

## Team status
- status: DONE
- blocker: none
