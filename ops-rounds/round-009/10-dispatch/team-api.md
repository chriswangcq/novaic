# Round 009 Dispatch - API Team

## Objective
Finalize API governance references and stabilize smoke behavior.

## Mandatory Tasks
1. Perform full scan to ensure no round-specific governance references remain in API docs.
2. Keep gateway smoke replay green and attach one fresh run.
3. Document final smoke port strategy as stable policy.

## Acceptance Commands
- `bash novaic-backend/scripts/smoke_gateway_independent_startup.sh`
- `rg "round-00|storage-contract-diff-latest|STORAGE_SCHEMA_OWNERSHIP_CHECKLIST" novaic-backend/docs contracts .github -g "*.md" -g "*.yml"`

## Due / Status
- due: 2026-02-24 18:00
- status: DONE

## Execution Breakdown

### Task 1: Full scan for round-specific governance references in API docs
- owner: API Team
- due: 2026-02-24 16:30
- status: DONE
- evidence:
  - commands:
    - `rg "ops-rounds/round-[0-9]{3}|round-[0-9]{3}" novaic-backend/docs -g "*.md"`
    - `rg "round-00|storage-contract-diff-latest|STORAGE_SCHEMA_OWNERSHIP_CHECKLIST" novaic-backend/docs contracts .github -g "*.md" -g "*.yml"`
  - result_summary:
    - API docs scan found no round-specific governance references.
    - governance refs in contracts/CI point to stable evergreen paths.
  - artifacts:
    - `novaic-backend/docs/gateway-api-surface-inventory-round002.md`
    - `contracts/STORAGE_SCHEMA_GOVERNANCE.md`
    - `contracts/README.md`
    - `.github/workflows/ci.yml`
  - docs:
    - `ops-rounds/round-009/20-reports/team-api-report.md`
- dependencies:
  - none
- risk_level: P1

### Task 2: Replay gateway smoke and attach fresh output
- owner: API Team
- due: 2026-02-24 17:00
- status: DONE
- evidence:
  - commands:
    - `bash novaic-backend/scripts/smoke_gateway_independent_startup.sh`
  - result_summary:
    - `PASS: startup smoke base 61900`
    - `PASS: runtime-orchestrator healthy on 61993`
    - `PASS: gateway healthy on 61999`
    - `PASS: gateway API root reachable`
  - artifacts:
    - `novaic-backend/scripts/smoke_gateway_independent_startup.sh`
  - docs:
    - `ops-rounds/round-009/20-reports/team-api-report.md`
- dependencies:
  - local Python runtime + temp dir write access
- risk_level: P1

### Task 3: Document final smoke port strategy as stable policy
- owner: API Team
- due: 2026-02-24 17:30
- status: DONE
- evidence:
  - commands:
    - `rg "gateway-smoke-port-strategy" ops-rounds/governance novaic-backend/scripts .github -g "*.md" -g "*.sh" -g "*.yml"`
  - result_summary:
    - stable policy file added and referenced by governance index and smoke script docs
    - CI gateway-smoke section references canonical stable policy
  - artifacts:
    - `ops-rounds/governance/gateway-smoke-port-strategy.md`
    - `ops-rounds/governance/governance-index.md`
    - `novaic-backend/scripts/smoke_gateway_independent_startup.sh`
    - `novaic-backend/scripts/README.md`
    - `.github/workflows/ci.yml`
  - docs:
    - `ops-rounds/round-009/20-reports/team-api-report.md`
- dependencies:
  - none
- risk_level: P1
