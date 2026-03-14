# Storage-A/B Operator Runbook & Final Handoff Checklist
<!-- version: v1.0.0 | finalized: 2026-02-19 | round: 009 | owner: Storage-A/B Team -->

## Purpose

This is the **final operator handoff checklist** for the Storage-A/B governance
track. Any new operator can use this document to:

1. Understand what governance controls are in place
2. Replay all validation checks from scratch
3. Verify ownership and sign-off status
4. Locate all canonical artifacts

Related comprehensive doc: `contracts/STORAGE_GOVERNANCE_AUDIT_HANDOFF.md`

---

## Section A — Ownership Table

| Party | Role | Status | Signed On |
|---|---|---|---|
| Platform Team | Contract scaffolding, CI validation conventions | SIGNED | 2026-02-20 |
| API Team | Endpoint/payload evolution, review gate | SIGNED | 2026-02-19 |
| Storage-A/B Team | Schema baseline, diff evidence, governance scripts | SIGNED | 2026-02-19 |

Checklist file: `contracts/STORAGE_SCHEMA_OWNERSHIP_CHECKLIST.md` — **CLOSED**

Any breaking schema change requires re-approval from all three parties.
Policy: `contracts/STORAGE_SCHEMA_GOVERNANCE.md § Ownership and Approval`

---

## Section B — Canonical Artifact Locations

| Artifact | Stable Path | Notes |
|---|---|---|
| Governance policy | `contracts/STORAGE_SCHEMA_GOVERNANCE.md` | v1.1.0, STORAGE-GOV-001 |
| API schema (JSON Schema) | `contracts/schema/storage-api.v1.schema.json` | v1.0.0 |
| Schema changelog | `contracts/STORAGE_SCHEMA_CHANGELOG.md` | Update on every schema change |
| Ownership checklist | `contracts/STORAGE_SCHEMA_OWNERSHIP_CHECKLIST.md` | CLOSED |
| Evergreen diff evidence | `contracts/evidence/storage-contract-diff-latest.md` | Overwritten on each diff run |
| Audit handoff package | `contracts/STORAGE_GOVERNANCE_AUDIT_HANDOFF.md` | Full index |
| This runbook | `contracts/STORAGE_OPERATOR_RUNBOOK.md` | Operator quick-ref |

---

## Section C — Replay Checklist

Run from repo root. All commands must exit 0.

### C1. Backup / Restore Validation
```bash
bash novaic-backend/scripts/storage_ab_validate_restore.sh
```
Expected output:
```
VALIDATION_OK=true
```
Evidence path: `ops-rounds/<round>/20-reports/team-storage-ab-validation-latest.md`

- [ ] VALIDATION_OK=true
- [ ] file restore check: PASS
- [ ] db restore check: PASS

---

### C2. Service Smoke Test
```bash
bash novaic-backend/scripts/storage_ab_smoke.sh
```
Expected output:
```
SMOKE_OK=true
```

- [ ] SMOKE_OK=true
- [ ] file_service_health: PASS
- [ ] tool_result_service_health: PASS
- [ ] file_write_read: PASS
- [ ] tool_result_write_read: PASS

---

### C3. Contract Diff Against Schema
```bash
bash novaic-backend/scripts/storage_ab_contract_diff.sh \
  --schema-path contracts/schema/storage-api.v1.schema.json
```
Expected output:
```
CONTRACT_DIFF_OK=true
```

- [ ] CONTRACT_DIFF_OK=true
- [ ] schema_version_check: PASS
- [ ] schema_owner_check: PASS
- [ ] All endpoints: missing=[], extra=[]
- [ ] Evergreen evidence refreshed: `contracts/evidence/storage-contract-diff-latest.md`

---

### C4. Governance Guardrail (STORAGE-GOV-001)
```bash
python3 novaic-backend/scripts/storage_ab_governance_check.py
```
Expected output:
```
governance_guardrail: PASS
exit_code: 0
```

- [ ] governance_guardrail: PASS
- [ ] exit_code: 0
- [ ] simulation_note line present

---

## Section D — CI Guardrail Reference

| CI Job | File | Trigger Condition |
|---|---|---|
| `storage-contract-governance` | `.github/workflows/ci.yml` | Any push/PR to `main` |

Fails when:
- `contracts/schema/storage-api.v1.schema.json` changes without updated diff evidence
- Schema changes without updated `contracts/STORAGE_SCHEMA_CHANGELOG.md`
- Evidence file lacks `schema_version_check: PASS` or `schema_owner_check: PASS`

Local simulation: `python3 novaic-backend/scripts/storage_ab_governance_check.py`

---

## Section E — Schema Change Procedure

When a storage schema change is needed:

1. [ ] Open PR with schema file change
2. [ ] Run: `bash novaic-backend/scripts/storage_ab_contract_diff.sh --schema-path contracts/schema/storage-api.v1.schema.json`
3. [ ] Verify: `schema_version_check: PASS`, `schema_owner_check: PASS`
4. [ ] Update `contracts/STORAGE_SCHEMA_CHANGELOG.md` with change entry
5. [ ] Update `x-contract-version` in `contracts/schema/storage-api.v1.schema.json`
6. [ ] Get approval from all three parties (Platform / API / Storage-A/B)
7. [ ] Merge — CI `storage-contract-governance` job will verify automatically

Minor bump policy: `contracts/STORAGE_SCHEMA_GOVERNANCE.md § Minor bump`
Major bump policy: `contracts/STORAGE_SCHEMA_GOVERNANCE.md § Major bump`

---

## Section F — Handoff Attestation

| Field | Value |
|---|---|
| Prepared by | Storage-A/B Team |
| Finalized on | 2026-02-19 |
| Final round | 009 |
| Governance policy version | v1.1.0 |
| Schema version | v1.0.0 |
| All P0/P1 risks | CLOSED |
| Ownership checklist | CLOSED (tri-party signed) |
| CI guardrail | ACTIVE |
| Evidence policy | EVERGREEN (no round rollover debt) |
| Local CI simulation | CANONICAL (STORAGE-GOV-001) |
| Handoff status | **FINAL — ready for operations handoff** |
