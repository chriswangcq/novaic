# Round 002 Dispatch - Runtime Team

## Objective
Resolve startup health instability and prove deterministic lifecycle behavior under repeated operations.

## Hard Tasks
1. Fix failing runtime startup/healthcheck scenario from Week 1.
2. Add repeatable startup verification (run at least 3 consecutive pass runs).
3. Extend lifecycle consistency tests for repeated start/stop and concurrent requests.
4. Publish startup troubleshooting notes and known failure signatures.

## Acceptance Criteria
- Startup/healthcheck contract tests pass.
- Repeat-run startup verification passes 3/3 runs.
- Lifecycle test suite includes concurrent/repeat edge cases.

## Required Evidence
- test commands and pass summary
- startup verification report
- troubleshooting doc path

## Status
- owner: Runtime Team
- due: 2026-02-26
- status: DONE
- evidence:
  - `novaic-backend/tests/unit/runtime_orchestrator/test_runtime_lifecycle_consistency.py` (new lifecycle consistency baseline tests)
  - `novaic-backend/runtime_orchestrator/LIFECYCLE_STATE_MODEL.md` (lifecycle contract doc)
  - `novaic-backend/tests/contract/test_runtime_orchestrator_process_startup.py` (startup/healthcheck contract stabilization)
  - `ops-rounds/round-002/20-reports/runtime-startup-verification-report.md` (3/3 repeat-run verification)
  - `ops-rounds/round-002/20-reports/team-runtime-report.md` (execution report)
- dependencies:
  - API Team (gateway/runtime forwarding contract verification)
  - Platform Team (contract baseline updates)
- risk_level: P1
