# Round 009 Dispatch - Runtime Team

## Objective
Advance probe-safety governance from path policy to sustainable telemetry-backed checks.

## Mandatory Tasks
1. Add warning telemetry/report for non-allowlisted localhost probe patterns.
2. Replay startup and lifecycle suites after telemetry hook.
3. Publish final runtime operability runbook section for non-author replay.

## Acceptance Commands
- `bash scripts/tools/ci_guard_localhost_probe_safety.sh`
- `pytest -q tests/contract/test_runtime_orchestrator_process_startup.py`
- `pytest -q tests/unit/runtime_orchestrator/test_runtime_lifecycle_consistency.py`

## Due / Status
- due: 2026-02-24 18:00
- status: DONE

## Execution Tracking
- Task 1: Add warning telemetry/report for non-allowlisted localhost probe patterns.
  - owner: Runtime Team
  - due: 2026-02-24 18:00
  - status: DONE
  - evidence:
    - command: `PROBE_GUARD_REPORT_PATH="../ops-rounds/round-009/20-reports/runtime-probe-telemetry.md" bash scripts/tools/ci_guard_localhost_probe_safety.sh`
    - result: `localhost probe safety guard passed (allowlisted=1, checked=1, warnings=0)`
    - result: `telemetry_report=../ops-rounds/round-009/20-reports/runtime-probe-telemetry.md`
    - artifacts/docs:
      - `novaic-backend/scripts/tools/ci_guard_localhost_probe_safety.sh`
      - `ops-rounds/round-009/20-reports/runtime-probe-telemetry.md`
  - dependencies:
    - none
  - risk_level: P1

- Task 2: Replay startup and lifecycle suites after telemetry hook.
  - owner: Runtime Team
  - due: 2026-02-24 18:00
  - status: DONE
  - evidence:
    - command: `pytest -q tests/contract/test_runtime_orchestrator_process_startup.py`
    - result: `3 passed`
    - command: `pytest -q tests/unit/runtime_orchestrator/test_runtime_lifecycle_consistency.py`
    - result: `5 passed`
    - artifacts/docs:
      - `novaic-backend/tests/contract/test_runtime_orchestrator_process_startup.py`
      - `novaic-backend/tests/unit/runtime_orchestrator/test_runtime_lifecycle_consistency.py`
  - dependencies:
    - none
  - risk_level: P1

- Task 3: Publish final runtime operability runbook section for non-author replay.
  - owner: Runtime Team
  - due: 2026-02-24 18:00
  - status: DONE
  - evidence:
    - docs:
      - `ops-rounds/round-009/20-reports/runtime-operability-runbook-final.md`
  - dependencies:
    - none
  - risk_level: P1
