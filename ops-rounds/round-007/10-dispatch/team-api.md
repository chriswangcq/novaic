# Round 007 Dispatch - API Team

## Objective
Close ownership co-sign dependency and keep gateway smoke stable.

## Mandatory Tasks
1. Complete storage ownership checklist co-sign closure with Platform/Storage.
2. Replay gateway smoke and attach fresh output.
3. Ensure evergreen storage evidence references remain valid in docs/CI.

## Acceptance Commands
- `bash novaic-backend/scripts/smoke_gateway_independent_startup.sh`
- `rg "STORAGE_SCHEMA_OWNERSHIP_CHECKLIST|storage-contract-diff-latest" contracts .github novaic-backend/docs -g "*.md" -g "*.yml"`

## Due / Status
- due: 2026-02-23 18:00
- status: DONE

## Execution Breakdown

### Task 1: Complete storage checklist tri-party co-sign
- owner: API Team
- due: 2026-02-23 18:00
- status: DONE
- evidence:
  - commands:
    - `rg "SIGNED|PENDING" contracts/STORAGE_SCHEMA_OWNERSHIP_CHECKLIST.md`
  - result_summary:
    - Platform + API + Storage-A/B are all `SIGNED`.
    - governance trace evidence is available at evergreen policy path and round evidence report.
  - artifacts:
    - `contracts/STORAGE_SCHEMA_OWNERSHIP_CHECKLIST.md`
  - docs:
    - `ops-rounds/round-007/20-reports/team-api-report.md`
- dependencies:
  - none
- risk_level: P1

### Task 2: Replay gateway smoke and attach fresh output
- owner: API Team
- due: 2026-02-23 17:00
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
    - `ops-rounds/round-007/20-reports/team-api-report.md`
- dependencies:
  - local Python runtime + temp directory permissions
- risk_level: P1

### Task 3: Ensure evergreen storage evidence references remain valid
- owner: API Team
- due: 2026-02-23 17:30
- status: DONE
- evidence:
  - commands:
    - `rg "STORAGE_SCHEMA_OWNERSHIP_CHECKLIST|storage-contract-diff-latest" contracts .github novaic-backend/docs -g "*.md" -g "*.yml"`
    - `python - <<'PY' ... validate governance refs in gateway inventory doc ... PY`
  - result_summary:
    - `rg` confirms references in contracts governance docs and CI workflow
    - python doc check confirms gateway inventory doc contains checklist + evergreen evidence refs
  - artifacts:
    - `contracts/STORAGE_SCHEMA_GOVERNANCE.md`
    - `contracts/README.md`
    - `.github/workflows/ci.yml`
    - `novaic-backend/docs/gateway-api-surface-inventory-round002.md`
  - docs:
    - `ops-rounds/round-007/20-reports/team-api-report.md`
- dependencies:
  - none
- risk_level: P1
