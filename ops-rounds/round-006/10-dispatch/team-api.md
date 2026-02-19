# Round 006 Dispatch - API Team

## Objective
Close co-sign and evergreen evidence-path migration with executable proof.

## Mandatory Tasks
1. Complete storage ownership checklist co-sign closure (Platform + API + Storage-A/B).
2. Implement dual-write or evergreen evidence path for storage governance outputs.
3. Replay gateway smoke and attach fresh output.

## Acceptance Commands
- `bash novaic-backend/scripts/smoke_gateway_independent_startup.sh`
- `rg "STORAGE_SCHEMA_OWNERSHIP_CHECKLIST|storage-contract-diff" contracts ops-rounds .github -g "*.md" -g "*.yml"`

## Due / Status
- due: 2026-02-24 18:00
- status: DONE_WITH_GAPS

## Execution Breakdown

### Task 1: Complete ownership checklist tri-party co-sign
- owner: API Team
- due: 2026-02-24 18:00
- status: IN_PROGRESS
- evidence:
  - commands:
    - `rg "STORAGE_SCHEMA_OWNERSHIP_CHECKLIST" contracts ops-rounds -g "*.md"`
  - result_summary:
    - Platform + API are signed; Storage-A/B signature is still pending.
  - artifacts:
    - `contracts/STORAGE_SCHEMA_OWNERSHIP_CHECKLIST.md`
    - `ops-rounds/round-006/20-reports/team-platform-report.md`
  - docs:
    - `ops-rounds/round-006/20-reports/team-api-report.md`
- dependencies:
  - Storage-A/B Team co-sign update on checklist
- risk_level: P1

### Task 2: Implement evergreen evidence path governance
- owner: API Team
- due: 2026-02-24 16:00
- status: DONE
- evidence:
  - commands:
    - `bash novaic-backend/scripts/storage_ab_contract_diff.sh --report-path ops-rounds/round-006/20-reports/team-storage-ab-contract-diff-latest.md --schema-path contracts/schema/storage-api.v1.schema.json`
  - result_summary:
    - evergreen evidence written to `contracts/evidence/storage-contract-diff-latest.md`
    - round mirror evidence written to Round 006 report path
    - CI guardrail uses evergreen evidence path
  - artifacts:
    - `contracts/evidence/storage-contract-diff-latest.md`
    - `contracts/STORAGE_SCHEMA_GOVERNANCE.md`
    - `.github/workflows/ci.yml`
    - `novaic-backend/scripts/storage_ab_contract_diff.sh`
  - docs:
    - `ops-rounds/round-006/20-reports/team-storage-ab-contract-diff-latest.md`
- dependencies:
  - shared governance alignment with Platform + Storage-A/B
- risk_level: P1

### Task 3: Replay gateway smoke with fresh output
- owner: API Team
- due: 2026-02-24 17:00
- status: DONE
- evidence:
  - commands:
    - `bash novaic-backend/scripts/smoke_gateway_independent_startup.sh`
  - result_summary:
    - `PASS: startup smoke base 61900`
    - `PASS: runtime-orchestrator healthy`
    - `PASS: gateway healthy`
    - `PASS: gateway API root reachable`
  - artifacts:
    - `novaic-backend/scripts/smoke_gateway_independent_startup.sh`
  - docs:
    - `ops-rounds/round-006/20-reports/team-api-report.md`
- dependencies:
  - local Python runtime and temp dir access
- risk_level: P1
