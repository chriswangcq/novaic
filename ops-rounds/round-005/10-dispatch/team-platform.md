# Round 005 Dispatch - Platform Team

## Objective
Eliminate governance debt by codifying contract ownership and compatibility evidence standards.

## Mandatory Tasks
1. Define and publish breaking-change approval policy for `contracts/schema/storage-api.v1.schema.json`.
2. Deliver auditable evidence list for `>=5` component compatibility consumption (with exact workflow/file references).
3. Add CI check that fails when contract version changes without changelog/update note.

## Acceptance Commands
- `rg "storage-api.v1.schema.json|compatibility.yaml|compatibility-matrix" contracts .github`
- `pytest -q tests/unit/common/test_strict_config.py`

## Due / Status
- due: 2026-02-25 18:00
- status: IN_PROGRESS

## Task Tracking
- task: mandatory-1-breaking-change-approval-policy
  owner: Platform Team
  due: 2026-02-25 18:00
  status: DONE
  evidence:
    - `contracts/STORAGE_SCHEMA_GOVERNANCE.md`
    - `contracts/STORAGE_SCHEMA_CHANGELOG.md`
    - `contracts/schema/storage-api.v1.schema.json`
  dependencies:
    - API + Storage-A/B ownership confirmation
  risk_level: medium

- task: mandatory-2-compatibility-consumption-5-components
  owner: Platform Team
  due: 2026-02-25 18:00
  status: IN_PROGRESS
  evidence:
    - `.github/workflows/ci.yml` (`compatibility-matrix`)
    - `compatibility.yaml`
  dependencies:
    - component owners provide workflow-level adoption evidence
  risk_level: high

- task: mandatory-3-contract-version-guardrail-ci
  owner: Platform Team
  due: 2026-02-25 18:00
  status: DONE
  evidence:
    - `.github/workflows/ci.yml` (job: `storage-contract-governance`)
    - `contracts/STORAGE_SCHEMA_CHANGELOG.md`
    - `ops-rounds/round-005/20-reports/team-storage-ab-contract-diff-latest.md` (required evidence path)
  dependencies:
    - finalize changelog/update-note convention
  risk_level: medium
