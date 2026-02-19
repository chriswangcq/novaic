# Round 004 Dispatch - Platform Team

## Objective
Close platform carry-over and unblock Gate B final closure.

## Mandatory Tasks
1. Publish Round003 contract field diff summary file.
2. Provide evidence for `compatibility.yaml` consumption by >=5 components.
3. Coordinate with Storage/API to land storage contract schema under `contracts/`.

## Acceptance Commands
- `rg "compatibility.yaml|compatibility-matrix" .github novaic-backend`
- `rg "storage|file-service|tool-result" contracts -g "*.yaml" -g "*.json"`

## Due / Status
- due: 2026-02-23 18:00
- status: IN_PROGRESS

## Task Tracking
- task: mandatory-1-round003-contract-diff-summary
  owner: Platform Team
  due: 2026-02-23 18:00
  status: IN_PROGRESS
  evidence:
    - `ops-rounds/round-004/20-reports/platform-round003-contract-diff-summary.md`
  dependencies:
    - align with API/Storage contract field owners
  risk_level: medium

- task: mandatory-2-matrix-consumption-5-components
  owner: Platform Team
  due: 2026-02-23 18:00
  status: IN_PROGRESS
  evidence:
    - `.github/workflows/ci.yml` (`compatibility-matrix`)
    - `compatibility.yaml` (5 repo entries)
  dependencies:
    - component owners provide component-level CI adoption evidence
  risk_level: high

- task: mandatory-3-storage-contract-schema-landing
  owner: Platform Team
  due: 2026-02-23 18:00
  status: IN_PROGRESS
  evidence:
    - `contracts/openapi/storage-contracts.v1.yaml`
    - `contracts/schema/storage-artifact.v1.schema.json`
  dependencies:
    - Storage-A/B + API confirm executable diff scope
  risk_level: medium
