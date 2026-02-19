# Round 004 Report - API Team

## Completed Work
- Replayed gateway isolated startup smoke and kept reproducibility evidence fresh.
- Synchronized API inventory contract references to latest contract files in `contracts/`.
- Co-authored storage contract schema field set and validated it via executable diff run.
- Kept forbidden cross-repo source import scan clean for `gateway/`.

## Command Evidence + Pass Summary
- `bash scripts/smoke_gateway_independent_startup.sh`
  - result summary:
    - `PASS: runtime-orchestrator healthy on 61993`
    - `PASS: gateway healthy on 61999`
    - `PASS: gateway API root reachable`
- `bash novaic-backend/scripts/storage_ab_contract_diff.sh --report-path ops-rounds/round-004/20-reports/team-storage-ab-contract-diff-round004.md`
  - result summary:
    - `CONTRACT_DIFF_OK=true`
    - `EVIDENCE_REPORT=ops-rounds/round-004/20-reports/team-storage-ab-contract-diff-round004.md`
- `rg "storage|file-service|tool-result" novaic-backend/docs contracts -g "*.md" -g "*.yaml" -g "*.json"`
  - result summary: storage contract references present in docs/contracts; no command error in report build context
- `rg "^\s*(from\s+(task_queue|runtime_orchestrator|tools_server)\b|import\s+(task_queue|runtime_orchestrator|tools_server)\b)" novaic-backend/gateway --glob "**/*.py"`
  - result summary: `No matches found`

## Artifacts / Docs Paths
- `.github/workflows/ci.yml` (includes `gateway-smoke` job)
- `novaic-backend/scripts/smoke_gateway_independent_startup.sh`
- `novaic-backend/docs/gateway-api-surface-inventory-round002.md` (updated contract reference paths)
- `contracts/schema/storage-api.v1.schema.json` (co-authored storage field baseline)
- `contracts/openapi/storage-contracts.v1.yaml`
- `contracts/schema/storage-artifact.v1.schema.json`
- `ops-rounds/round-004/20-reports/team-storage-ab-contract-diff-round004.md`
- `ops-rounds/round-004/10-dispatch/team-api.md`

## Acceptance Mapping
- Keep gateway smoke CI green and attach one fresh run.
  - status: DONE
  - evidence: smoke command output + CI workflow includes `gateway-smoke` job
- Sync API inventory references to latest contracts paths.
  - status: DONE
  - evidence: updated references in `gateway-api-surface-inventory-round002.md`
- Co-author storage contract schema fields with Storage/Platform.
  - status: DONE
  - evidence: `storage-api.v1.schema.json` field set + executable diff report (`CONTRACT_DIFF_OK=true`)

## Risks / Blockers
- Current blockers (11:00 sync): none.
- Residual risk: smoke script fixed ports (`61993-61999`) may collide on busy runners.

## Decision Needed
- issue: whether to keep fixed-port smoke script or require dynamic port allocation before Gate freeze.
- options:
  - A) Keep fixed ports, rely on low collision probability.
  - B) Switch to dynamic free-port allocation with lock file and health guards.
  - C) Keep fixed ports but add one retry with alternate port range.
- recommendation:
  - B) Switch to dynamic allocation in next patch window for better CI stability.
- impact:
  - Positive: lower flaky rate in shared runners, fewer false negatives.
  - Cost: small script complexity increase and one extra verification run.

## Self Status
- status: DONE
