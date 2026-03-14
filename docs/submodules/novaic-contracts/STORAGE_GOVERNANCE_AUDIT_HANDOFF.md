# Storage Governance Audit Handoff Package
<!-- generated: 2026-02-19 | round: 008 | owner: Storage-A/B Team -->

## Status: FINAL

This document is the canonical single-file audit handoff for the Storage-A/B
governance track. It indexes every governance artifact, its location, and
its final status. It can be handed off to any new operator or auditor.

---

## 1. Governance Policy

| Document | Path | Version | Status |
|---|---|---|---|
| Schema Governance | `contracts/STORAGE_SCHEMA_GOVERNANCE.md` | v1.1.0 | FINAL |
| Schema Changelog | `contracts/STORAGE_SCHEMA_CHANGELOG.md` | — | ACTIVE |
| Ownership Checklist | `contracts/STORAGE_SCHEMA_OWNERSHIP_CHECKLIST.md` | — | CLOSED |
| Contracts README | `contracts/README.md` | — | ACTIVE |

Key governance rules:
- Minor/major bump policy defined (§ Version Bump Policy)
- Tri-party approval required for breaking changes (§ Ownership and Approval)
- Schema changes must ship with updated diff evidence + changelog (§ Required Evidence)
- CI guardrail enforces evidence co-delivery (§ CI Guardrail)
- Local CI simulation approved as equivalent path: rule **STORAGE-GOV-001** (§ Local CI Simulation Policy)

---

## 2. Contract Schema

| Artifact | Path | Version |
|---|---|---|
| API Schema (JSON Schema) | `contracts/schema/storage-api.v1.schema.json` | v1.0.0 |
| x-contract-version | `v1.0.0` | — |
| x-contract-owners | Platform Team, API Team, Storage-A/B Team | — |

---

## 3. Evergreen Evidence (Stable Paths)

These paths never roll over with rounds. CI and scripts always target these.

| Evidence Type | Evergreen Path | Last Run | Result |
|---|---|---|---|
| Contract Diff | `contracts/evidence/storage-contract-diff-latest.md` | 2026-02-19 | PASS |

---

## 4. Operational Scripts

| Script | Path | Purpose |
|---|---|---|
| Backup | `novaic-backend/scripts/storage_ab_backup.sh` | Full backup of file-service + tool-result-service |
| Restore | `novaic-backend/scripts/storage_ab_restore.sh` | Restore from backup directory |
| Validate Restore | `novaic-backend/scripts/storage_ab_validate_restore.sh` | End-to-end backup→restore→verify cycle |
| Smoke Test | `novaic-backend/scripts/storage_ab_smoke.sh` | Health + read/write smoke for both services |
| Contract Diff | `novaic-backend/scripts/storage_ab_contract_diff.sh` | Live API vs schema diff (dual-write to evergreen) |
| Governance Check | `novaic-backend/scripts/storage_ab_governance_check.py` | STORAGE-GOV-001 local CI simulation |

All scripts exit 0 on success, non-zero on failure. Output variables:
- `BACKUP_OK=true` / `RESTORE_OK=true` / `VALIDATION_OK=true`
- `SMOKE_OK=true` / `CONTRACT_DIFF_OK=true`
- `governance_guardrail: PASS` / `exit_code: 0`

---

## 5. CI Guardrail

File: `.github/workflows/ci.yml`, job: `storage-contract-governance`

Fails when:
- `contracts/schema/storage-api.v1.schema.json` changes without updated `contracts/evidence/storage-contract-diff-latest.md`
- Schema changes without updated `contracts/STORAGE_SCHEMA_CHANGELOG.md`
- Evidence file lacks `schema_version_check: PASS` or `schema_owner_check: PASS`

Local simulation: `python3 novaic-backend/scripts/storage_ab_governance_check.py`
Governance policy reference: `contracts/STORAGE_SCHEMA_GOVERNANCE.md § CI Guardrail`

---

## 6. Ownership

| Party | Sign Status | Date |
|---|---|---|
| Platform Team | SIGNED | 2026-02-20 |
| API Team | SIGNED | 2026-02-19 |
| Storage-A/B Team | SIGNED | 2026-02-19 |

Checklist: `contracts/STORAGE_SCHEMA_OWNERSHIP_CHECKLIST.md` — **CLOSED**

---

## 7. Round-by-Round Evidence Trail

| Round | Diff Evidence | Validation Evidence | Smoke Evidence | CI Trace |
|---|---|---|---|---|
| Round 003 | `ops-rounds/round-003/20-reports/team-storage-ab-contract-diff-latest.md` | `ops-rounds/round-003/20-reports/team-storage-ab-validation-latest.md` | `ops-rounds/round-003/20-reports/team-storage-ab-smoke-latest.md` | — |
| Round 004 | `ops-rounds/round-004/20-reports/team-storage-ab-contract-diff-latest.md` | `ops-rounds/round-004/20-reports/team-storage-ab-validation-latest.md` | `ops-rounds/round-004/20-reports/team-storage-ab-smoke-latest.md` | — |
| Round 005 | `ops-rounds/round-005/20-reports/team-storage-ab-contract-diff-latest.md` | `ops-rounds/round-005/20-reports/team-storage-ab-validation-latest.md` | `ops-rounds/round-005/20-reports/team-storage-ab-smoke-latest.md` | — |
| Round 006 | `ops-rounds/round-006/20-reports/team-storage-ab-contract-diff-latest.md` | `ops-rounds/round-006/20-reports/team-storage-ab-validation-latest.md` | `ops-rounds/round-006/20-reports/team-storage-ab-smoke-latest.md` | `ops-rounds/round-006/20-reports/team-storage-ab-ci-trace-attempt.txt` |
| Round 007 | `ops-rounds/round-007/20-reports/team-storage-ab-contract-diff-latest.md` | `ops-rounds/round-007/20-reports/team-storage-ab-validation-latest.md` | `ops-rounds/round-007/20-reports/team-storage-ab-smoke-latest.md` | `ops-rounds/round-007/20-reports/team-storage-ab-ci-governance-trace.md` |
| Round 008 | `ops-rounds/round-008/20-reports/team-storage-ab-contract-diff-latest.md` | `ops-rounds/round-008/20-reports/team-storage-ab-validation-latest.md` | `ops-rounds/round-008/20-reports/team-storage-ab-smoke-latest.md` | `ops-rounds/round-008/20-reports/team-storage-ab-ci-governance-trace.md` |

---

## 8. Quick Replay Checklist (for new operators)

```bash
# From repo root:

# 1. Validate backup/restore cycle
bash novaic-backend/scripts/storage_ab_validate_restore.sh

# 2. Smoke test both services
bash novaic-backend/scripts/storage_ab_smoke.sh

# 3. Contract diff against canonical schema
bash novaic-backend/scripts/storage_ab_contract_diff.sh \
  --schema-path contracts/schema/storage-api.v1.schema.json

# 4. Governance guardrail simulation
python3 novaic-backend/scripts/storage_ab_governance_check.py

# All commands should exit 0 and print PASS/OK lines.
```

---

## 9. Handoff Attestation

- Prepared by: Storage-A/B Team
- Date: 2026-02-19
- Round: 008 (final governance closure)
- All P0/P1 risks: CLOSED
- Ownership checklist: CLOSED (tri-party signed)
- CI guardrail: ACTIVE in `ci.yml`
- Evidence policy: EVERGREEN (no round rollover debt)
- Local CI simulation rule: CANONICAL (STORAGE-GOV-001, policy version v1.1.0)
