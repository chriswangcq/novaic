# Round 005 Report - Storage-A/B Team

## Completed Work
- Added storage schema governance policy:
  - `contracts/STORAGE_SCHEMA_GOVERNANCE.md`
- Added explicit contract metadata in storage schema:
  - `contracts/schema/storage-api.v1.schema.json` (`x-contract-version`, `x-contract-owners`)
- Extended executable diff script with version/owner governance checks:
  - `novaic-backend/scripts/storage_ab_contract_diff.sh`
- Added CI guardrail job to fail when schema changes without updated diff evidence:
  - `.github/workflows/ci.yml` (`storage-contract-governance`)
- Replayed critical storage paths and generated fresh Round 005 evidence docs.

## Command Evidence + Pass Summary
- `bash novaic-backend/scripts/storage_ab_contract_diff.sh --report-path ops-rounds/round-005/20-reports/team-storage-ab-contract-diff-latest.md --schema-path contracts/schema/storage-api.v1.schema.json`
  - result: `CONTRACT_DIFF_OK=true`
  - summary: contract matrix complete, `schema_version_check: PASS`, `schema_owner_check: PASS`
- `bash novaic-backend/scripts/storage_ab_validate_restore.sh --report-path ops-rounds/round-005/20-reports/team-storage-ab-validation-latest.md`
  - result: `VALIDATION_OK=true`
  - summary: restore replay passed for file + sqlite checks
- `bash novaic-backend/scripts/storage_ab_smoke.sh --report-path ops-rounds/round-005/20-reports/team-storage-ab-smoke-latest.md`
  - result: `SMOKE_OK=true`
  - summary: health + read/write replay passed

## Artifacts / Docs Paths
- contracts:
  - `contracts/STORAGE_SCHEMA_GOVERNANCE.md`
  - `contracts/schema/storage-api.v1.schema.json`
  - `contracts/README.md`
- scripts:
  - `novaic-backend/scripts/storage_ab_contract_diff.sh`
  - `novaic-backend/scripts/storage_ab_validate_restore.sh`
  - `novaic-backend/scripts/storage_ab_smoke.sh`
- CI:
  - `.github/workflows/ci.yml`
- evidence docs:
  - `ops-rounds/round-005/20-reports/team-storage-ab-contract-diff-latest.md`
  - `ops-rounds/round-005/20-reports/team-storage-ab-validation-latest.md`
  - `ops-rounds/round-005/20-reports/team-storage-ab-smoke-latest.md`

## Acceptance Mapping
- Mandatory Task 1 (version policy + migration notes):
  - status: DONE
  - evidence: `contracts/STORAGE_SCHEMA_GOVERNANCE.md`
- Mandatory Task 2 (version/owner checks in diff output):
  - status: DONE
  - evidence: `team-storage-ab-contract-diff-latest.md`
- Mandatory Task 3 (CI fail on schema change without diff evidence):
  - status: IN_PROGRESS
  - evidence: CI workflow logic added; pending first remote CI pass record

## Risks / Blockers
- No local execution blocker.
- Risk: CI guardrail has been implemented but still needs first real GitHub Actions pass/fail trace for closure evidence.

## Decision Needed
- issue:
  - Should storage contract governance gate apply only to `round-005` evidence path, or to a stable evergreen path (e.g. `contracts/evidence/storage-contract-diff-latest.md`) to avoid round rollover debt?
- options:
  - A) Keep round-specific evidence path in CI (`ops-rounds/round-005/20-reports/...`)
  - B) Move CI to evergreen evidence path and keep round files as mirrors
  - C) Require both round file + evergreen file updates
- recommendation:
  - B) Move CI enforcement to evergreen path, then auto-sync/copy into round reports.
- impact:
  - Positive: removes round rollover churn and lowers false CI failures in future rounds.
  - Cost: one-time script/report path refactor across Platform/API/Storage.
- owner:
  - Platform Team + API Team + Storage-A/B Team
- deadline:
  - 2026-02-20 18:00

## Self Status
- status: DONE_WITH_GAPS
