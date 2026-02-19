# Round 002 Dispatch - Platform Team

## Objective
Turn shared-kernel and governance assets from bootstrap into actively consumed standards.

## Hard Tasks
1. Migrate core shared modules into `novaic-shared-kernel/src/common` (not bridge-only).
2. Publish `shared-kernel v0.1.0rc2` and migration notes.
3. Ensure at least 5 team-owned components consume `compatibility.yaml` checks.
4. Upgrade contract baseline files with concrete required fields from Week 1 findings.

## Task Execution Status
- task: hard-task-1-core-module-migration
  owner: Platform Team
  due: 2026-02-26
  status: IN_PROGRESS
  evidence:
    - `novaic-shared-kernel/src/common/config.py`
    - `novaic-shared-kernel/src/common/strict_config.py`
    - `novaic-shared-kernel/src/common/db/`
    - `novaic-shared-kernel/src/common/http/`
    - `novaic-shared-kernel/src/common/utils/time.py`
  dependencies:
    - verify imports against active backend call paths
  risk_level: medium

- task: hard-task-2-publish-rc2
  owner: Platform Team
  due: 2026-02-26
  status: PLANNED
  evidence: []
  dependencies:
    - hard-task-1-core-module-migration
  risk_level: high

- task: hard-task-3-matrix-consumption-5-components
  owner: Platform Team
  due: 2026-02-26
  status: IN_PROGRESS
  evidence:
    - `.github/workflows/ci.yml` contains `compatibility-matrix` gate
  dependencies:
    - component owners adopt templates/checks
  risk_level: high

- task: hard-task-4-contract-baseline-upgrade
  owner: Platform Team
  due: 2026-02-26
  status: IN_PROGRESS
  evidence:
    - `contracts/openapi/gateway-public.v1.yaml`
    - `contracts/openapi/runtime-orchestrator-internal.v1.yaml`
    - `contracts/schema/task-message.v1.schema.json`
    - `contracts/schema/subagent-status.v1.schema.json`
  dependencies:
    - API Team + Runtime Team provide required-field deltas
  risk_level: medium

## Acceptance Criteria
- `shared-kernel` imports work without monorepo relative path dependency.
- `compatibility.yaml` CI checks are referenced in at least 5 components.
- Contract files are versioned and referenced by API/Runtime teams.

## Required Evidence
- package version and publish proof
- paths of migrated shared modules
- list of repos/components consuming matrix checks
- contract diff summary

## Status
- owner: Platform Team
- due: 2026-02-26
- status: IN_PROGRESS
