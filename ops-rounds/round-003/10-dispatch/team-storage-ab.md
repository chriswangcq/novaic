# Round 003 Dispatch - Storage-A/B Team

## Objective
Close remaining contract alignment and CI evidence gaps after P0 closure.

## Mandatory Tasks
1. Finalize command-backed contract mismatch matrix (matched/missing/extra fields).
2. Add CI evidence for smoke and validation scripts.
3. Keep backup/restore validation evidence fresh with one rerun.

## Acceptance Commands
- `bash novaic-backend/scripts/storage_ab_validate_restore.sh`
- `bash novaic-backend/scripts/storage_ab_smoke.sh`
- `pytest -q tests/unit/file_service tests/unit/tool_result_service`

## Due / Status
- due: 2026-02-24 18:00
- status: DONE_WITH_GAPS

## Execution Breakdown

### Task 1: Contract mismatch matrix
- owner: Storage-A/B Team
- due: 2026-02-24 14:00
- status: DONE
- evidence:
  - commands:
    - `bash novaic-backend/scripts/storage_ab_contract_diff.sh`
  - result_summary:
    - matrix generated with matched/missing/extra fields for File Service and Tool Result Service payloads
  - artifacts:
    - `novaic-backend/scripts/storage_ab_contract_diff.sh`
  - docs:
    - `ops-rounds/round-003/20-reports/team-storage-ab-contract-diff-latest.md`
- dependencies:
  - storage contract baseline in `contracts/`
- risk_level: P1

### Task 2: CI evidence for smoke and validation scripts
- owner: Storage-A/B Team
- due: 2026-02-24 16:00
- status: DONE
- evidence:
  - commands:
    - `bash novaic-backend/scripts/storage_ab_validate_restore.sh --report-path ops-rounds/round-003/20-reports/team-storage-ab-validation-latest.md`
    - `bash novaic-backend/scripts/storage_ab_smoke.sh --report-path ops-rounds/round-003/20-reports/team-storage-ab-smoke-latest.md`
    - `pytest -q tests/unit/file_service tests/unit/tool_result_service`
  - result_summary:
    - `VALIDATION_OK=true`
    - `SMOKE_OK=true`
    - `2 passed` for unit tests
  - artifacts:
    - `novaic-backend/scripts/storage_ab_validate_restore.sh`
    - `novaic-backend/scripts/storage_ab_smoke.sh`
    - `novaic-backend/tests/unit/file_service/test_basic.py`
    - `novaic-backend/tests/unit/tool_result_service/test_tool_result_basic.py`
  - docs:
    - `ops-rounds/round-003/20-reports/team-storage-ab-validation-latest.md`
    - `ops-rounds/round-003/20-reports/team-storage-ab-smoke-latest.md`
- dependencies:
  - local python test environment
- risk_level: P1

### Task 3: Refresh backup/restore validation evidence
- owner: Storage-A/B Team
- due: 2026-02-24 17:00
- status: DONE
- evidence:
  - commands:
    - `bash novaic-backend/scripts/storage_ab_validate_restore.sh --report-path ops-rounds/round-003/20-reports/team-storage-ab-validation-latest.md`
  - result_summary:
    - restore validation rerun completed with file + db recovery checks passed
  - artifacts:
    - `novaic-backend/scripts/storage_ab_backup.sh`
    - `novaic-backend/scripts/storage_ab_restore.sh`
  - docs:
    - `ops-rounds/round-003/20-reports/team-storage-ab-validation-latest.md`
- dependencies:
  - temporary local workspace and sqlite availability
- risk_level: P1

## Blockers (11:00 sync)
- owner: Storage-A/B Team
- due: 2026-02-19 11:00
- status: BLOCKED
- evidence:
  - commands:
    - `ls contracts/openapi`
    - `ls contracts/schema`
  - result_summary:
    - no dedicated storage API schema exists in `contracts/` yet
  - docs:
    - `ops-rounds/round-003/20-reports/team-storage-ab-contract-diff-latest.md`
- dependencies:
  - Platform/API provide storage contract baseline in `contracts/`
- risk_level: P1
