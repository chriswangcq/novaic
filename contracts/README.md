# Contracts Baseline (Week 1)

This directory contains baseline contract files for cross-repo integration.

## Structure

- `openapi/`: service HTTP API contracts (OpenAPI 3.x)
- `schema/`: payload-level JSON Schemas

## Versioning

- File suffix `v1` indicates first stable contract family.
- Breaking changes require new versioned files (e.g. `v2`).

## Ownership

- Platform Team: contract scaffolding and validation conventions
- API Team / Runtime Team: endpoint and payload evolution with review
- Storage-A/B Team: storage contract baseline (`schema/storage-api.v1.schema.json`) and executable diff evidence

## Storage Contract Governance
- Policy doc: `contracts/STORAGE_SCHEMA_GOVERNANCE.md` (policy-version: v1.1.0)
- Canonical local-CI-simulation rule: STORAGE-GOV-001 (see policy doc)
- Ownership checklist: `contracts/STORAGE_SCHEMA_OWNERSHIP_CHECKLIST.md` (status: CLOSED)
- Evergreen diff evidence: `contracts/evidence/storage-contract-diff-latest.md`
- Changelog: `contracts/STORAGE_SCHEMA_CHANGELOG.md`
- Audit handoff package: `contracts/STORAGE_GOVERNANCE_AUDIT_HANDOFF.md`
- Operator runbook & final checklist: `contracts/STORAGE_OPERATOR_RUNBOOK.md`
- Governance check script: `novaic-backend/scripts/storage_ab_governance_check.py`
- Storage schema must include explicit version and owners metadata.
