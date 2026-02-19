# Round 005 Dispatch - API Team

## Objective
Prevent API drift by aligning docs/contracts and hardening startup smoke reliability.

## Mandatory Tasks
1. Replace fixed-port smoke behavior with deterministic free-port allocation or fallback strategy.
2. Add CI assertion that API inventory contract references must exist.
3. Co-sign storage contract ownership checklist with Platform/Storage.

## Acceptance Commands
- `bash scripts/smoke_gateway_independent_startup.sh`
- `rg "storage|gateway-api-surface|contracts/" novaic-backend/docs .github`

## Due / Status
- due: 2026-02-25 18:00
- status: IN_PROGRESS

## Task Tracking
- task: mandatory-1-smoke-port-strategy-hardening
  owner: API Team
  due: 2026-02-25 18:00
  status: DONE
  evidence:
    - `novaic-backend/scripts/smoke_gateway_independent_startup.sh`
    - `bash novaic-backend/scripts/smoke_gateway_independent_startup.sh`
  result_summary:
    - replaced fixed single-port dependency with deterministic fallback bases (`61900/62000/62100`)
    - replay result: PASS on first base (`61900`)

- task: mandatory-2-api-inventory-contract-ci-assertion
  owner: API Team
  due: 2026-02-25 18:00
  status: DONE
  evidence:
    - `.github/workflows/ci.yml` (`Validate API inventory contract references`)
  result_summary:
    - CI now fails when required contract refs are missing from API inventory doc
    - CI also validates referenced contract files exist on disk

- task: mandatory-3-storage-contract-ownership-cosign
  owner: API Team
  due: 2026-02-25 18:00
  status: IN_PROGRESS
  evidence:
    - `contracts/STORAGE_SCHEMA_OWNERSHIP_CHECKLIST.md`
    - `contracts/STORAGE_SCHEMA_GOVERNANCE.md`
  dependencies:
    - Platform Team co-sign
    - Storage-A/B Team co-sign
  risk_level: medium
