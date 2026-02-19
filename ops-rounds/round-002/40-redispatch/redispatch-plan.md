# Round 002 Redispatch Plan

## Review Trigger
- Source findings: `ops-rounds/round-002/30-review/reviewer-findings.md`
- Reason: unresolved P0 items and multiple P1 evidence/completion gaps.

## Redispatch Window
- Start: 2026-02-20
- Hard deadline: 2026-02-22 18:00
- Review checkpoint: daily 11:00

## Decision Rule
- Any open P0 after deadline => Round 002 result must remain `FAIL`.
- P1 can roll over only if explicitly approved with evidence-backed rationale.

## P0 Mandatory Fixes

### 1) Runtime Team - Startup health instability closure
- finding_reference: P0 runtime startup healthcheck failures
- owner: Runtime Team
- due: 2026-02-22 18:00
- status: PLANNED
- mandatory_fix_tasks:
  1. Fix startup/health path so failing startup contract tests pass.
  2. Add and run repeatable startup verification for 3 consecutive successful runs.
  3. Attach failure root cause and fix note to troubleshooting doc.
- acceptance_commands:
  - `pytest -q tests/contract/test_runtime_orchestrator_process_startup.py`
  - `pytest -q tests/contract/test_internal_api_contract_baseline.py`
  - `bash scripts/run_runtime_startup_verify_3x.sh`
- pass_criteria:
  - startup contract tests pass
  - 3/3 startup verification pass
  - report updated with concrete evidence paths

### 2) Storage-A/B Team - Executable backup/restore and smoke closure
- finding_reference: P0 storage executable delivery missing
- owner: Storage-A/B Team
- due: 2026-02-22 18:00
- status: PLANNED
- mandatory_fix_tasks:
  1. Deliver runnable backup and restore scripts for file service and tool-result service.
  2. Execute one full restore drill and publish command + output summary.
  3. Add health and read/write smoke tests and include pass summary.
- acceptance_commands:
  - `bash scripts/storage/backup_file_service.sh && bash scripts/storage/restore_file_service.sh`
  - `bash scripts/storage/backup_tool_result_service.sh && bash scripts/storage/restore_tool_result_service.sh`
  - `pytest -q tests/unit/file_service tests/unit/tool_result_service`
  - `bash scripts/storage/smoke_storage_services.sh`
- pass_criteria:
  - backup/restore scripts run successfully
  - one restore drill evidence exists
  - smoke tests pass and are documented

## P1 Mandatory Fixes

### 3) API Team - Evidence path and deliverable validity correction
- finding_reference: P1 missing/invalid doc evidence paths in DONE items
- owner: API Team
- due: 2026-02-21 18:00
- status: PLANNED
- mandatory_fix_tasks:
  1. Create missing env spec and API inventory files at reported paths, or update report to truthful paths/status.
  2. Revalidate independent startup smoke script and include latest pass summary.
- acceptance_commands:
  - `bash scripts/smoke_gateway_independent_startup.sh`
  - `rg "gateway-env-spec-round002|gateway-api-surface-inventory-round002" ops-rounds/round-002/20-reports/team-api-report.md novaic-backend/docs`
- pass_criteria:
  - evidence paths resolve to existing files
  - report status aligns with evidence

### 4) Platform Team - Bridge reduction and matrix adoption proof
- finding_reference: P1 shared-kernel still bridge-heavy and adoption evidence incomplete
- owner: Platform Team
- due: 2026-02-22 18:00
- status: PLANNED
- mandatory_fix_tasks:
  1. Move at least one core shared module from bridge into real `novaic-shared-kernel/src/common` implementation.
  2. Provide evidence for `compatibility.yaml` checks consumed by at least 5 components.
  3. Publish contract field-diff summary from Round 001 to Round 002.
- acceptance_commands:
  - `python3 - <<'PY' ... import common ... PY`
  - `rg "compatibility.yaml|compatibility-matrix" .github novaic-backend`
- pass_criteria:
  - module migration evidence exists
  - 5-component adoption evidence documented
  - contract diff summary file exists

### 5) Desktop Team - RC artifact and clean-machine proof
- finding_reference: P1 RC installer and clean-machine validation missing
- owner: Desktop Team
- due: 2026-02-22 18:00
- status: PLANNED
- mandatory_fix_tasks:
  1. Produce Round 002 RC installer artifact with build summary.
  2. Run clean-machine startup checklist and publish results.
  3. Link diagnostics logs and triage outcomes.
- acceptance_commands:
  - `bash build.sh` 
  - `cargo check --manifest-path "novaic-app/src-tauri/Cargo.toml"`
- pass_criteria:
  - artifact path exists
  - clean-machine checklist evidence exists
  - startup diagnostics logs referenced

### 6) Agent Runtime Team - Cross-process idempotency closure
- finding_reference: P1 idempotency still in-process only
- owner: Agent Runtime Team
- due: 2026-02-22 18:00
- status: PLANNED
- mandatory_fix_tasks:
  1. Implement persistent or queue-level idempotency guard.
  2. Add cross-process/restart duplicate-task tests.
  3. Add retry visibility field (`next_retry_at` or equivalent) and evidence.
- acceptance_commands:
  - `pytest -q novaic-backend/tests/unit/task_queue/test_retry_policy_and_idempotency.py`
  - `pytest -q novaic-backend/tests/integration/task_queue/test_cross_process_idempotency.py`
- pass_criteria:
  - cross-process idempotency tests pass
  - retry visibility behavior is observable in report and code

### 7) Tools Team - Reliability hard evidence extension
- finding_reference: P1 missing OS-level leak probe and config schema integration
- owner: Tools Team
- due: 2026-02-22 18:00
- status: DONE
- mandatory_fix_tasks:
  1. Add one OS-level fd/process leak probe script with one pass run report.
  2. Integrate reliability config keys into schema/startup validation.
- acceptance_commands:
  - `pytest -q tests/unit/tools_server/test_api_reliability_controls.py`
  - `bash scripts/tools/leak_probe.sh`
- pass_criteria:
  - leak probe evidence attached
  - config schema validation evidence attached
- closure_evidence:
  - `bash scripts/tools/leak_probe.sh` => PASS (`fd delta=0`, `leaked=[]`)
  - `pytest -q tests/unit/common/test_strict_config.py` => `3 passed`
  - report: `ops-rounds/round-002/20-reports/team-tools-report.md`

## Reporting Requirements
- Each team must update corresponding file in `ops-rounds/round-002/20-reports/` by 18:00 daily.
- Each claimed DONE item must include commands, output summary, and artifact/doc paths.

## Current Plan Status
- status: IN_PROGRESS
- last_updated_by: AI Assistant
