# Round 003 Dispatch - Platform Team

## Objective
Finish shared-kernel de-bridge and prove matrix/contract adoption.

## Mandatory Tasks
1. Reduce remaining bridge imports and migrate at least 2 additional common modules into `novaic-shared-kernel/src/common`.
2. Provide evidence that `compatibility.yaml` checks are consumed by >=5 components.
3. Publish Round 002 -> Round 003 contract field diff summary.

## Acceptance Commands
- `python3 - <<'PY' ... import common.config, common.db, common.http ... PY`
- `rg "compatibility.yaml|compatibility-matrix" .github novaic-backend`

## Due / Status
- due: 2026-02-24 18:00
- status: IN_PROGRESS

## Task Tracking
- task: mandatory-1-debridge-plus-two-modules
  owner: Platform Team
  due: 2026-02-24 18:00
  status: IN_PROGRESS
  evidence:
    - `novaic-shared-kernel/src/common/config.py`
    - `novaic-shared-kernel/src/common/db/`
    - `novaic-shared-kernel/src/common/http/`
  dependencies:
    - common modules migration plan
  risk_level: medium

- task: mandatory-2-matrix-consumption-5-components
  owner: Platform Team
  due: 2026-02-24 18:00
  status: IN_PROGRESS
  evidence:
    - `.github/workflows/ci.yml` (`compatibility-matrix`)
  dependencies:
    - component owners align CI adoption
  risk_level: high

- task: mandatory-3-contract-diff-summary
  owner: Platform Team
  due: 2026-02-24 18:00
  status: PLANNED
  evidence: []
  dependencies:
    - API + Runtime + Storage field updates
  risk_level: medium
