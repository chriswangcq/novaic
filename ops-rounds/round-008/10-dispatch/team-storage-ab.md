# Round 008 Dispatch - Storage-A/B Team

## Objective
Finalize CI-trace governance policy and keep storage guardrails fully green.

## Mandatory Tasks
1. Convert "local CI simulation as approved equivalent" into canonical governance rule.
2. Replay contract diff/validate/smoke and refresh evergreen evidence artifacts.
3. Provide one final governance trace package for audit handoff.

## Acceptance Commands
- `bash novaic-backend/scripts/storage_ab_contract_diff.sh --schema-path contracts/schema/storage-api.v1.schema.json`
- `bash novaic-backend/scripts/storage_ab_validate_restore.sh`
- `bash novaic-backend/scripts/storage_ab_smoke.sh`

## Due / Status
- due: 2026-02-23 18:00
- status: DONE

## Evidence

### Task 1 — Canonical governance rule
- command: Updated `contracts/STORAGE_SCHEMA_GOVERNANCE.md` (policy-version: v1.1.0, effective: 2026-02-19)
- created: `novaic-backend/scripts/storage_ab_governance_check.py` (STORAGE-GOV-001 standalone script)
- updated: `.github/workflows/ci.yml` comment to reference canonical policy path
- result: STORAGE-GOV-001 rule is self-contained, versioned, and referenced by CI

### Task 2 — Replay acceptance commands (all PASS)
| Command | Result | Evidence |
|---|---|---|
| `bash novaic-backend/scripts/storage_ab_contract_diff.sh --schema-path contracts/schema/storage-api.v1.schema.json` | CONTRACT_DIFF_OK=true | `ops-rounds/round-008/20-reports/team-storage-ab-contract-diff-latest.md` |
| `bash novaic-backend/scripts/storage_ab_validate_restore.sh` | VALIDATION_OK=true | `ops-rounds/round-008/20-reports/team-storage-ab-validation-latest.md` |
| `bash novaic-backend/scripts/storage_ab_smoke.sh` | SMOKE_OK=true | `ops-rounds/round-008/20-reports/team-storage-ab-smoke-latest.md` |
| `python3 novaic-backend/scripts/storage_ab_governance_check.py` | governance_guardrail: PASS | `ops-rounds/round-008/20-reports/team-storage-ab-ci-governance-trace.md` |

Evergreen evidence refreshed: `contracts/evidence/storage-contract-diff-latest.md`

### Task 3 — Audit handoff package
- artifact: `contracts/STORAGE_GOVERNANCE_AUDIT_HANDOFF.md`
- contents: policy index, schema table, evergreen evidence paths, script index, CI guardrail spec, ownership status, round-by-round evidence trail, quick-replay checklist, handoff attestation

## P0/P1 Status
- All P0 risks: CLOSED
- All P1 risks: CLOSED
