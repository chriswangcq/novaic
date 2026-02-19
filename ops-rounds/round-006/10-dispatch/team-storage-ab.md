# Round 006 Dispatch - Storage-A/B Team

## Objective
Finish CI closure evidence and migrate governance evidence path to stable standard.

## Mandatory Tasks
1. Capture first remote CI pass/fail trace for `storage-contract-governance` and attach evidence.
2. Implement agreed evidence-path policy (evergreen or dual-write transition).
3. Replay diff/validate/smoke scripts and verify outputs remain green.

## Acceptance Commands
- `bash novaic-backend/scripts/storage_ab_contract_diff.sh`
- `bash novaic-backend/scripts/storage_ab_validate_restore.sh`
- `bash novaic-backend/scripts/storage_ab_smoke.sh`

## Due / Status
- due: 2026-02-24 18:00
- status: DONE_WITH_GAPS

## Execution Breakdown

### Task 1: Capture first remote CI trace for `storage-contract-governance`
- owner: Storage-A/B Team
- due: 2026-02-24 12:00
- status: BLOCKED
- evidence:
  - commands:
    - `gh run list --workflow "CI" --limit 5`
    - `if command -v gh >/dev/null 2>&1; then gh run list --workflow "CI" --limit 5; else echo "gh command not found"; fi`
  - result_summary:
    - local environment missing `gh` CLI (`EXIT_CODE=127`), unable to fetch remote run trace from here
  - artifacts:
    - `ops-rounds/round-006/20-reports/team-storage-ab-ci-trace-attempt.txt`
  - docs:
    - `ops-rounds/round-006/20-reports/team-storage-ab-report.md`
- dependencies:
  - GitHub CLI availability or alternate remote CI evidence feed
- risk_level: P1

### Task 2: Apply evidence-path policy to stable standard
- owner: Storage-A/B Team
- due: 2026-02-24 14:00
- status: DONE
- evidence:
  - commands:
    - `bash novaic-backend/scripts/storage_ab_contract_diff.sh --report-path ops-rounds/round-006/20-reports/team-storage-ab-contract-diff-latest.md --schema-path contracts/schema/storage-api.v1.schema.json`
  - result_summary:
    - dual-write path implemented: evergreen + round mirror
    - CI guardrail switched to evergreen evidence path
  - artifacts:
    - `contracts/STORAGE_SCHEMA_GOVERNANCE.md`
    - `contracts/evidence/storage-contract-diff-latest.md`
    - `novaic-backend/scripts/storage_ab_contract_diff.sh`
    - `.github/workflows/ci.yml`
  - docs:
    - `ops-rounds/round-006/20-reports/team-storage-ab-contract-diff-latest.md`
- dependencies:
  - governance alignment with Platform/API
- risk_level: P1

### Task 3: Replay diff/validate/smoke and verify green
- owner: Storage-A/B Team
- due: 2026-02-24 16:00
- status: DONE
- evidence:
  - commands:
    - `bash novaic-backend/scripts/storage_ab_contract_diff.sh --report-path ops-rounds/round-006/20-reports/team-storage-ab-contract-diff-latest.md --schema-path contracts/schema/storage-api.v1.schema.json`
    - `bash novaic-backend/scripts/storage_ab_validate_restore.sh --report-path ops-rounds/round-006/20-reports/team-storage-ab-validation-latest.md`
    - `bash novaic-backend/scripts/storage_ab_smoke.sh --report-path ops-rounds/round-006/20-reports/team-storage-ab-smoke-latest.md`
  - result_summary:
    - `CONTRACT_DIFF_OK=true`
    - `VALIDATION_OK=true`
    - `SMOKE_OK=true`
  - artifacts:
    - `ops-rounds/round-006/20-reports/team-storage-ab-contract-diff-latest.md`
    - `ops-rounds/round-006/20-reports/team-storage-ab-validation-latest.md`
    - `ops-rounds/round-006/20-reports/team-storage-ab-smoke-latest.md`
  - docs:
    - `contracts/evidence/storage-contract-diff-latest.md`
- dependencies:
  - local Python runtime and temp directory write access
- risk_level: P1
