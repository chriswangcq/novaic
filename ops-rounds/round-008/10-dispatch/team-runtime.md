# Round 008 Dispatch - Runtime Team

## Objective
Finalize probe-safety governance rollout with explicit path policy.

## Mandatory Tasks
1. Implement approved guard scope expansion (`startup`/`health` allowlist policy).
2. Replay startup and lifecycle checks after expansion.
3. Publish final probe-guard policy doc with scope, owner, and review cadence.

## Acceptance Commands
- `bash scripts/tools/ci_guard_localhost_probe_safety.sh`
- `pytest -q tests/contract/test_runtime_orchestrator_process_startup.py`
- `pytest -q tests/unit/runtime_orchestrator/test_runtime_lifecycle_consistency.py`

## Due / Status
- due: 2026-02-23 18:00
- status: DONE

## Execution Tracking
- Task 1: Implement approved guard scope expansion (`startup`/`health` allowlist policy).
  - owner: Runtime Team
  - due: 2026-02-23 18:00
  - status: DONE
  - evidence:
    - command: `bash scripts/tools/ci_guard_localhost_probe_safety.sh`
    - result: `localhost probe safety guard passed (allowlisted=1, checked=1)`
    - artifacts/docs:
      - `novaic-backend/scripts/tools/ci_guard_localhost_probe_safety.sh`
      - `ops-rounds/round-008/20-reports/runtime-probe-guard-policy-final.md`
  - dependencies:
    - none
  - risk_level: P1

- Task 2: Replay startup and lifecycle checks after expansion.
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

- Task 3: Publish final probe-guard policy doc with scope, owner, and review cadence.
  - owner: Runtime Team
  - due: 2026-02-23 18:00
  - status: DONE
  - evidence:
    - docs:
      - `ops-rounds/round-008/20-reports/runtime-probe-guard-policy-final.md`
  - dependencies:
    - none
  - risk_level: P1
