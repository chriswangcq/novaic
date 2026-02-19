# Round 003 Dispatch - Runtime Team

## Objective
Keep startup reliability green and harden concurrent lifecycle contention checks.

## Mandatory Tasks
1. Keep startup contract tests green and provide one fresh execution proof.
2. Add one more concurrent lifecycle contention test case (CAS/status update race).
3. Publish CI guard note to prevent proxy-related localhost regression.

## Acceptance Commands
- `pytest -q tests/contract/test_runtime_orchestrator_process_startup.py`
- `pytest -q tests/unit/runtime_orchestrator/test_runtime_lifecycle_consistency.py`

## Due / Status
- due: 2026-02-24 18:00
- status: DONE

## Execution Tracking
- Task 1: Keep startup contract tests green and provide one fresh execution proof.
  - owner: Runtime Team
  - due: 2026-02-24 18:00
  - status: DONE
  - evidence:
    - command: `pytest -q tests/contract/test_runtime_orchestrator_process_startup.py`
    - result: `3 passed`
    - artifacts/docs:
      - `novaic-backend/tests/contract/test_runtime_orchestrator_process_startup.py`
      - `ops-rounds/round-003/20-reports/team-runtime-report.md`
  - dependencies:
    - none
  - risk_level: P1

- Task 2: Add one more concurrent lifecycle contention test case (CAS/status update race).
  - owner: Runtime Team
  - due: 2026-02-24 18:00
  - status: DONE
  - evidence:
    - command: `pytest -q tests/unit/runtime_orchestrator/test_runtime_lifecycle_consistency.py`
    - result: `5 passed`
    - artifacts/docs:
      - `novaic-backend/tests/unit/runtime_orchestrator/test_runtime_lifecycle_consistency.py`
      - `ops-rounds/round-003/20-reports/team-runtime-report.md`
  - dependencies:
    - runtime orchestrator repository layer stability
  - risk_level: P1

- Task 3: Publish CI guard note to prevent proxy-related localhost regression.
  - owner: Runtime Team
  - due: 2026-02-24 18:00
  - status: DONE
  - evidence:
    - docs:
      - `ops-rounds/round-003/20-reports/runtime-ci-guard-note.md`
      - `novaic-backend/tests/contract/test_runtime_orchestrator_process_startup.py`
  - dependencies:
    - none
  - risk_level: P1
