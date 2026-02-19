# Round 009 Dispatch - Storage-A/B Team

## Objective
Deliver final storage governance audit package in stable canonical form.

## Mandatory Tasks
1. Ensure STORAGE-GOV-001 equivalent-evidence rule is canonical in governance doc.
2. Replay diff/validate/smoke and refresh evergreen evidence artifacts.
3. Publish final audit handoff checklist with replay commands and ownership table.

## Acceptance Commands
- `bash novaic-backend/scripts/storage_ab_contract_diff.sh --schema-path contracts/schema/storage-api.v1.schema.json`
- `bash novaic-backend/scripts/storage_ab_validate_restore.sh`
- `bash novaic-backend/scripts/storage_ab_smoke.sh`

## Due / Status
- due: 2026-02-24 18:00
- status: DONE

## Evidence

### Task 1 — STORAGE-GOV-001 canonical verification
- verified: `contracts/STORAGE_SCHEMA_GOVERNANCE.md` at policy-version v1.1.0
- fixed: `novaic-backend/scripts/storage_ab_governance_check.py` DeprecationWarning (utcnow → datetime.now(UTC))
- updated: `contracts/README.md` — added references to audit handoff package, operator runbook, governance check script
- result: STORAGE-GOV-001 canonical, no dead references, all cross-refs consistent

### Task 2 — Acceptance commands (all PASS)
| Command | Result | Evidence |
|---|---|---|
| `bash novaic-backend/scripts/storage_ab_contract_diff.sh --schema-path contracts/schema/storage-api.v1.schema.json` | CONTRACT_DIFF_OK=true | `ops-rounds/round-009/20-reports/team-storage-ab-contract-diff-latest.md` |
| `bash novaic-backend/scripts/storage_ab_validate_restore.sh` | VALIDATION_OK=true | `ops-rounds/round-009/20-reports/team-storage-ab-validation-latest.md` |
| `bash novaic-backend/scripts/storage_ab_smoke.sh` | SMOKE_OK=true | `ops-rounds/round-009/20-reports/team-storage-ab-smoke-latest.md` |
| `python3 novaic-backend/scripts/storage_ab_governance_check.py` | governance_guardrail: PASS | `ops-rounds/round-009/20-reports/team-storage-ab-ci-governance-trace.md` |

Evergreen evidence refreshed: `contracts/evidence/storage-contract-diff-latest.md`

### Task 3 — Final audit handoff checklist
- created: `contracts/STORAGE_OPERATOR_RUNBOOK.md` (v1.0.0)
  - Section A: Ownership table (tri-party, all SIGNED)
  - Section B: Canonical artifact locations
  - Section C: Replay checklist (C1 validate / C2 smoke / C3 diff / C4 governance)
  - Section D: CI guardrail reference
  - Section E: Schema change procedure
  - Section F: Handoff attestation (FINAL)
- updated: `contracts/README.md` to index the runbook

## P0/P1 Status
- All P0 risks: CLOSED
- All P1 risks: CLOSED
