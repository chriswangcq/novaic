# Round 008 Dispatch - API Team

## Objective
Close API-side governance carry-over and ensure evergreen reference correctness.

## Mandatory Tasks
1. Update API report state from `DONE_WITH_GAPS` to factual state if closure evidence is complete.
2. Verify all governance references in API docs point to evergreen/stable paths.
3. Replay gateway smoke and attach final-round output.

## Acceptance Commands
- `bash novaic-backend/scripts/smoke_gateway_independent_startup.sh`
- `rg "STORAGE_SCHEMA_OWNERSHIP_CHECKLIST|storage-contract-diff-latest|governance" novaic-backend/docs contracts .github -g "*.md" -g "*.yml"`

## Due / Status
- due: 2026-02-23 18:00
- status: DONE

## Execution Breakdown

### Task 1: Update API carry-over report state to factual closure
- owner: API Team
- due: 2026-02-23 16:30
- status: DONE
- evidence:
  - commands:
    - `rg "SIGNED|PENDING" contracts/STORAGE_SCHEMA_OWNERSHIP_CHECKLIST.md`
    - `python - <<'PY' ... verify governance closure markers in policy + trace ... PY`
  - result_summary:
    - checklist confirms all three teams are `SIGNED`
    - governance policy contains canonical trace rule marker `STORAGE-GOV-001`
    - round trace contains `governance_guardrail: PASS` and `exit_code: 0`
  - artifacts:
    - `contracts/STORAGE_SCHEMA_OWNERSHIP_CHECKLIST.md`
    - `contracts/STORAGE_SCHEMA_GOVERNANCE.md`
    - `ops-rounds/round-007/20-reports/team-storage-ab-ci-governance-trace.md`
    - `ops-rounds/round-007/20-reports/team-api-report.md`
    - `ops-rounds/round-007/10-dispatch/team-api.md`
  - docs:
    - `ops-rounds/round-008/20-reports/team-api-report.md`
- dependencies:
  - none
- risk_level: P1

### Task 2: Verify API governance references are evergreen/stable
- owner: API Team
- due: 2026-02-23 17:00
- status: DONE
- evidence:
  - commands:
    - `rg "STORAGE_SCHEMA_OWNERSHIP_CHECKLIST|storage-contract-diff-latest|governance" novaic-backend/docs contracts .github -g "*.md" -g "*.yml"`
    - `python - <<'PY' ... validate API doc uses evergreen refs only ... PY`
  - result_summary:
    - references present in contracts governance docs and CI workflow
    - API inventory doc has checklist + evergreen diff refs and no round-specific storage governance path
  - artifacts:
    - `novaic-backend/docs/gateway-api-surface-inventory-round002.md`
    - `contracts/README.md`
    - `contracts/STORAGE_SCHEMA_GOVERNANCE.md`
    - `.github/workflows/ci.yml`
  - docs:
    - `ops-rounds/round-008/20-reports/team-api-report.md`
- dependencies:
  - none
- risk_level: P1

### Task 3: Replay gateway smoke final-round output
- owner: API Team
- due: 2026-02-23 17:30
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
    - `ops-rounds/round-008/20-reports/team-api-report.md`
- dependencies:
  - local Python runtime + temp dir write permission
- risk_level: P1
