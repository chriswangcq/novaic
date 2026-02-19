# Round 004 Dispatch - Storage-A/B Team

## Objective
Close storage contract gap and make Gate B fully passable.

## Mandatory Tasks
1. Work with Platform/API to publish storage contract schema under `contracts/`.
2. Re-run contract diff script against published schema and attach matched/missing/extra matrix.
3. Keep validate/smoke scripts green with one replay run.

## Acceptance Commands
- `bash novaic-backend/scripts/storage_ab_contract_diff.sh`
- `bash novaic-backend/scripts/storage_ab_validate_restore.sh`
- `bash novaic-backend/scripts/storage_ab_smoke.sh`

## Due / Status
- due: 2026-02-23 18:00
- status: DONE

## Execution Breakdown

### Task 1: Publish storage contract schema under `contracts/`
- owner: Storage-A/B Team
- due: 2026-02-23 12:00
- status: DONE
- evidence:
  - commands:
    - `bash novaic-backend/scripts/storage_ab_contract_diff.sh --report-path ops-rounds/round-004/20-reports/team-storage-ab-contract-diff-latest.md --schema-path contracts/schema/storage-api.v1.schema.json`
  - result_summary:
    - schema-backed contract diff command executed successfully
  - artifacts:
    - `contracts/schema/storage-api.v1.schema.json`
  - docs:
    - `contracts/README.md`
- dependencies:
  - Platform/API review and adoption in Gate B
- risk_level: P1

### Task 2: Re-run executable contract diff against published schema
- owner: Storage-A/B Team
- due: 2026-02-23 14:00
- status: DONE
- evidence:
  - commands:
    - `bash novaic-backend/scripts/storage_ab_contract_diff.sh --report-path ops-rounds/round-004/20-reports/team-storage-ab-contract-diff-latest.md --schema-path contracts/schema/storage-api.v1.schema.json`
  - result_summary:
    - `CONTRACT_DIFF_OK=true`
    - matched/missing/extra matrix generated with no missing fields
  - artifacts:
    - `novaic-backend/scripts/storage_ab_contract_diff.sh`
  - docs:
    - `ops-rounds/round-004/20-reports/team-storage-ab-contract-diff-latest.md`
- dependencies:
  - storage schema path stability in `contracts/schema/`
- risk_level: P1

### Task 3: Replay validate/smoke scripts
- owner: Storage-A/B Team
- due: 2026-02-23 16:00
- status: DONE
- evidence:
  - commands:
    - `bash novaic-backend/scripts/storage_ab_validate_restore.sh --report-path ops-rounds/round-004/20-reports/team-storage-ab-validation-latest.md`
    - `bash novaic-backend/scripts/storage_ab_smoke.sh --report-path ops-rounds/round-004/20-reports/team-storage-ab-smoke-latest.md`
  - result_summary:
    - `VALIDATION_OK=true`
    - `SMOKE_OK=true`
  - artifacts:
    - `novaic-backend/scripts/storage_ab_validate_restore.sh`
    - `novaic-backend/scripts/storage_ab_smoke.sh`
  - docs:
    - `ops-rounds/round-004/20-reports/team-storage-ab-validation-latest.md`
    - `ops-rounds/round-004/20-reports/team-storage-ab-smoke-latest.md`
- dependencies:
  - local runtime environment and temp directory write access
- risk_level: P1

## 11:00 Blocker Sync
- owner: Storage-A/B Team
- due: 2026-02-19 11:00
- status: DONE
- evidence:
  - commands:
    - `ls contracts/schema`
  - result_summary:
    - storage schema present at `contracts/schema/storage-api.v1.schema.json`
  - docs:
    - `ops-rounds/round-004/20-reports/team-storage-ab-report.md`
- dependencies:
  - none
- risk_level: P1
