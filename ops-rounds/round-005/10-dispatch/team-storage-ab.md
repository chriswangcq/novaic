# Round 005 Dispatch - Storage-A/B Team

## Objective
Eliminate contract drift debt with strict schema lifecycle and executable diff governance.

## Mandatory Tasks
1. Define schema version bump policy (minor vs major) and migration note requirements.
2. Extend `storage_ab_contract_diff.sh` output with explicit version and owner check.
3. Add CI run that fails if schema changed without updated diff evidence file.

## Acceptance Commands
- `bash novaic-backend/scripts/storage_ab_contract_diff.sh`
- `bash novaic-backend/scripts/storage_ab_validate_restore.sh`
- `bash novaic-backend/scripts/storage_ab_smoke.sh`

## Due / Status
- due: 2026-02-25 18:00
- status: DONE_WITH_GAPS

## Execution Breakdown

### Task 1: Schema version bump policy and migration note requirements
- owner: Storage-A/B Team
- due: 2026-02-25 12:00
- status: DONE
- evidence:
  - commands:
    - `bash novaic-backend/scripts/storage_ab_contract_diff.sh --report-path ops-rounds/round-005/20-reports/team-storage-ab-contract-diff-latest.md --schema-path contracts/schema/storage-api.v1.schema.json`
  - result_summary:
    - governance policy documented and schema metadata includes explicit version + owners
  - artifacts:
    - `contracts/STORAGE_SCHEMA_GOVERNANCE.md`
    - `contracts/schema/storage-api.v1.schema.json`
  - docs:
    - `contracts/README.md`
- dependencies:
  - Platform/API governance alignment
- risk_level: P1

### Task 2: Extend contract diff with version/owner check
- owner: Storage-A/B Team
- due: 2026-02-25 14:00
- status: DONE
- evidence:
  - commands:
    - `bash novaic-backend/scripts/storage_ab_contract_diff.sh --report-path ops-rounds/round-005/20-reports/team-storage-ab-contract-diff-latest.md --schema-path contracts/schema/storage-api.v1.schema.json`
  - result_summary:
    - `CONTRACT_DIFF_OK=true`
    - evidence includes `schema_version_check: PASS` and `schema_owner_check: PASS`
  - artifacts:
    - `novaic-backend/scripts/storage_ab_contract_diff.sh`
  - docs:
    - `ops-rounds/round-005/20-reports/team-storage-ab-contract-diff-latest.md`
- dependencies:
  - schema metadata fields remain stable
- risk_level: P1

### Task 3: CI guardrail for schema change without diff evidence
- owner: Storage-A/B Team
- due: 2026-02-25 16:00
- status: IN_PROGRESS
- evidence:
  - commands:
    - `bash novaic-backend/scripts/storage_ab_validate_restore.sh --report-path ops-rounds/round-005/20-reports/team-storage-ab-validation-latest.md`
    - `bash novaic-backend/scripts/storage_ab_smoke.sh --report-path ops-rounds/round-005/20-reports/team-storage-ab-smoke-latest.md`
  - result_summary:
    - storage replay checks remain green (`VALIDATION_OK=true`, `SMOKE_OK=true`)
    - CI workflow updated with `storage-contract-governance` job, pending first remote run evidence
  - artifacts:
    - `.github/workflows/ci.yml`
    - `ops-rounds/round-005/20-reports/team-storage-ab-validation-latest.md`
    - `ops-rounds/round-005/20-reports/team-storage-ab-smoke-latest.md`
  - docs:
    - `ops-rounds/round-005/20-reports/team-storage-ab-report.md`
- dependencies:
  - GitHub Actions run availability to collect pass evidence
- risk_level: P1

## 11:00 Blocker Sync
- owner: Storage-A/B Team
- due: 2026-02-19 11:00
- status: IN_PROGRESS
- evidence:
  - commands:
    - `ls contracts/schema`
    - `bash novaic-backend/scripts/storage_ab_contract_diff.sh --report-path ops-rounds/round-005/20-reports/team-storage-ab-contract-diff-latest.md --schema-path contracts/schema/storage-api.v1.schema.json`
  - result_summary:
    - no hard blocker on local execution; one decision required for approval authority and CI scope
  - docs:
    - `ops-rounds/round-005/20-reports/team-storage-ab-report.md`
- dependencies:
  - Platform/API governance decision
- risk_level: P1
