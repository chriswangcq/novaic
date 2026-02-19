# Round 005 Report - API Team

## Completed Work
- Hardened gateway independent startup smoke from single fixed-port dependency to deterministic fallback-base strategy:
  - `novaic-backend/scripts/smoke_gateway_independent_startup.sh`
- Added CI assertion to enforce API inventory contract references:
  - `.github/workflows/ci.yml` (`Validate API inventory contract references`)
- Landed API-side co-sign artifact for storage schema ownership:
  - `contracts/STORAGE_SCHEMA_OWNERSHIP_CHECKLIST.md`
  - `contracts/README.md` (governance reference link)

## Command Evidence + Pass Summary
- `bash novaic-backend/scripts/smoke_gateway_independent_startup.sh`
  - result: PASS
  - summary: runtime-orchestrator and gateway health checks passed; gateway API root reachable
- `python - <<'PY' ... validate inventory required refs + file existence ... PY`
  - result: `missing_in_doc=[]`, `missing_paths=[]`, `OK`
  - summary: inventory doc contains all required contract references and all referenced files exist
- `rg "storage|gateway-api-surface|contracts/"` (workspace scan via rg tool)
  - result: matched contract/governance references in docs + CI workflow
  - summary: new API inventory CI assertion and storage governance artifacts are discoverable

## Artifacts / Docs Paths
- scripts:
  - `novaic-backend/scripts/smoke_gateway_independent_startup.sh`
- CI:
  - `.github/workflows/ci.yml`
- contracts/docs:
  - `contracts/STORAGE_SCHEMA_OWNERSHIP_CHECKLIST.md`
  - `contracts/STORAGE_SCHEMA_GOVERNANCE.md`
  - `contracts/README.md`
  - `novaic-backend/docs/gateway-api-surface-inventory-round002.md`
- dispatch/report:
  - `ops-rounds/round-005/10-dispatch/team-api.md`
  - `ops-rounds/round-005/20-reports/team-api-report.md`

## Acceptance Mapping
- Mandatory Task 1 (smoke port strategy hardening):
  - status: DONE
  - evidence: fallback-base smoke script + local replay PASS
- Mandatory Task 2 (API inventory contract CI assertion):
  - status: DONE
  - evidence: workflow check for required refs and path existence
- Mandatory Task 3 (co-sign storage contract ownership checklist with Platform/Storage):
  - status: IN_PROGRESS
  - evidence: API-side checklist signed; waiting Platform + Storage-A/B co-sign closure

## Risks / Blockers
- Blocker: no code blocker on API side.
- Risk: final closure of mandatory task 3 depends on cross-team co-sign completion timing (Platform + Storage-A/B).
- Risk: current storage governance CI evidence path is round-specific and may introduce rollover maintenance debt.

## Decision Needed
- issue:
  - Should storage governance evidence gating move from round-specific path to an evergreen path to avoid per-round CI churn?
- options:
  - A) Keep round-specific path only (current behavior)
  - B) Switch to evergreen path only (for example `contracts/evidence/storage-contract-diff-latest.md`)
  - C) Enforce both round-specific + evergreen files during transition
- recommendation:
  - C) Use dual-write transition in Round 005, then deprecate round-specific CI dependency after teams validate.
- impact:
  - Positive: improves long-term CI stability and reduces round rollover debt.
  - Cost: one-time updates to scripts/workflow/report templates across Platform/API/Storage-A/B.
- owner:
  - Platform Team + API Team + Storage-A/B Team
- deadline:
  - 2026-02-20 18:00

## Self Status
- status: IN_PROGRESS
