# Round 007 Dispatch - Runtime Team

## Objective
Convert probe-safety decision into expanded implementation.

## Mandatory Tasks
1. Expand localhost probe guard scope per approved plan (runtime-only vs broader contract path).
2. Replay startup + lifecycle suites after guard update.
3. Publish one concise guard policy note with affected path scope.

## Acceptance Commands
- `pytest -q tests/contract/test_runtime_orchestrator_process_startup.py`
- `pytest -q tests/unit/runtime_orchestrator/test_runtime_lifecycle_consistency.py`
- `bash scripts/tools/ci_guard_localhost_probe_safety.sh`

## Due / Status
- due: 2026-02-23 18:00
- status: DONE

## Execution Tracking
- Task 1: Expand localhost probe guard scope per approved plan (runtime-only vs broader contract path).
  - owner: Runtime Team
  - due: 2026-02-23 18:00
  - status: DONE
  - evidence:
    - command: `bash scripts/tools/ci_guard_localhost_probe_safety.sh`
    - result: `localhost probe safety guard passed (scanned 6 contract tests)`
    - artifacts/docs:
      - `novaic-backend/scripts/tools/ci_guard_localhost_probe_safety.sh`
      - `ops-rounds/round-007/20-reports/runtime-probe-guard-policy.md`
  - dependencies:
    - none
  - risk_level: P1

- Task 2: Replay startup + lifecycle suites after guard update.
  - owner: Runtime Team
  - due: 2026-02-23 18:00
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

- Task 3: Publish one concise guard policy note with affected path scope.
  - owner: Runtime Team
  - due: 2026-02-23 18:00
  - status: DONE
  - evidence:
    - docs:
      - `ops-rounds/round-007/20-reports/runtime-probe-guard-policy.md`
  - dependencies:
    - none
  - risk_level: P1
