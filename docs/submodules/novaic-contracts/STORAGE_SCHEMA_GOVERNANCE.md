# Storage Schema Governance
<!-- policy-version: v1.1.0 | effective: 2026-02-19 | owners: Platform/API/Storage-A/B -->

## Scope
Applies to:
- `contracts/schema/storage-api.v1.schema.json`
- future storage schema files under `contracts/schema/storage-*.schema.json`

## Version Bump Policy

### Minor bump (vX.Y -> vX.Y+1)
Use when:
- adding optional fields
- adding non-breaking enums
- adding metadata fields that existing consumers can ignore

Required migration notes:
- affected schema file
- backward compatibility statement
- consumer impact summary

### Major bump (vX -> vX+1)
Use when:
- removing required fields
- renaming/removing semantic fields
- changing response shape in a breaking way

Required migration notes:
- old -> new mapping table
- compatibility window and rollout order
- rollback strategy
- explicit caller upgrade checklist

## Ownership and Approval
- required reviewers:
  - Platform Team
  - API Team
  - Storage-A/B Team
- any breaking change requires all three approvals.

## Required Evidence for Schema Changes
If storage schema changes, the same change set must include:
- updated executable diff evidence file:
  - `contracts/evidence/storage-contract-diff-latest.md`
- optional round mirror file (for round reporting traceability):
  - `ops-rounds/round-00X/20-reports/team-storage-ab-contract-diff-latest.md`
- updated changelog/update note file:
  - `contracts/STORAGE_SCHEMA_CHANGELOG.md`
- report lines:
  - `schema_version_check: PASS`
  - `schema_owner_check: PASS`

## CI Guardrail
CI fails when:
- storage schema file changed without updated diff evidence file
- storage schema file changed without updated changelog/update note file
- evidence file exists but lacks PASS lines for version/owner checks

## Remote CI Trace Export
- script: `novaic-backend/scripts/export_storage_governance_ci_evidence.py`
- output (evergreen): `ops-rounds/governance/storage-governance-ci-trace-latest.md`
- usage:
  - with `gh` auth: `python3 novaic-backend/scripts/export_storage_governance_ci_evidence.py`
  - without `gh`: set `GITHUB_TOKEN` and run the same command

## Evidence Path Policy
- Standard path is evergreen: `contracts/evidence/storage-contract-diff-latest.md`.
- Round reports can mirror the same evidence for traceability.
- CI enforcement uses evergreen path to avoid round rollover debt.

## Local CI Simulation Policy
<!-- canonical-rule: STORAGE-GOV-001 | effective: 2026-02-19 | approved-in: Round 007 -->

When `gh` CLI and `GITHUB_TOKEN` are unavailable, the following procedure
is the **canonical approved-equivalent evidence path** (rule STORAGE-GOV-001):

1. Extract the Python logic verbatim from
   `.github/workflows/ci.yml:storage-contract-governance`.
2. Execute it locally against the same `git diff HEAD~1 HEAD` context.
3. Capture full stdout + `exit_code` in:
   `ops-rounds/<round>/20-reports/team-storage-ab-ci-governance-trace.md`
4. The trace file MUST contain all three lines:
   - `governance_guardrail: PASS`
   - `exit_code: 0`
   - `simulation_note: local execution of storage-contract-governance CI job logic`

This rule is referenced by the CI workflow comment in
`.github/workflows/ci.yml` (job `storage-contract-governance`)
and verified by `novaic-backend/scripts/storage_ab_governance_check.py`.
