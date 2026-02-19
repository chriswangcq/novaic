# Governance Index (Stable Reference)

version: v1.0
status: active
canonical_entrypoint: ops-rounds/governance/governance-index.md
updated_at: 2026-02-20

## Purpose
Single stable entrypoint for active governance policies, checklists, scripts, and CI gates.

## Effective Rules
- compatibility counting effective rule:
  - `ops-rounds/governance/effective-compatibility-counting-rule.md`
- compatibility counting rule spec:
  - `ops-rounds/governance/compatibility-consumption-counting-rule.md`
- compatibility evidence latest:
  - `ops-rounds/governance/compatibility-consumption-evidence-latest.md`
- status codes:
  - `ops-rounds/governance/status-codes.md`

## Storage Governance
- schema governance policy:
  - `contracts/STORAGE_SCHEMA_GOVERNANCE.md`
- ownership checklist:
  - `contracts/STORAGE_SCHEMA_OWNERSHIP_CHECKLIST.md`
- schema changelog/update notes:
  - `contracts/STORAGE_SCHEMA_CHANGELOG.md`
- latest CI trace evidence:
  - `ops-rounds/governance/storage-governance-ci-trace-latest.md`

## Operability / Reliability Policies
- gateway smoke port strategy:
  - `ops-rounds/governance/gateway-smoke-port-strategy.md`
- desktop operability policy:
  - `ops-rounds/governance/desktop-operability-policy.md`
- desktop operator quick checklist:
  - `ops-rounds/governance/desktop-operator-quick-checklist.md`
- definition of done:
  - `ops-rounds/governance/dod-definition.md`
- severity definitions:
  - `ops-rounds/governance/severity.md`

## Automation and Scripts
- compatibility counting + evidence enforcement:
  - `.github/workflows/ci.yml` job `compatibility-matrix`
- storage governance schema guard:
  - `.github/workflows/ci.yml` job `storage-contract-governance`
- remote CI evidence exporter:
  - `novaic-backend/scripts/export_storage_governance_ci_evidence.py`

## Usage Rule
- Round reports should reference this index instead of duplicating policy paths.
