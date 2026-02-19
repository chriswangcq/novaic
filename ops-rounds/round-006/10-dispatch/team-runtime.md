# Round 006 Dispatch - Runtime Team

## Objective
Deliver implementation (not only reruns): enforce proxy-safe probe governance in reusable form.

## Mandatory Tasks
1. Implement shared proxy-safe probe helper module for startup/contract tests.
2. Add CI check preventing unsafe localhost probe usage in targeted test paths.
3. Execute one concurrent stress replay and attach deterministic result summary.

## Acceptance Commands
- `pytest -q tests/contract/test_runtime_orchestrator_process_startup.py`
- `pytest -q tests/unit/runtime_orchestrator/test_runtime_lifecycle_consistency.py`
- `rg "trust_env=False|local probe helper" novaic-backend/tests -g "*.py"`

## Due / Status
- due: 2026-02-24 18:00
- status: DONE

## Execution Tracking
- Task 1: Implement shared proxy-safe probe helper module for startup/contract tests.
  - owner: Runtime Team
  - due: 2026-02-24 18:00
  - status: DONE
  - evidence:
    - command: `pytest -q tests/contract/test_runtime_orchestrator_process_startup.py`
    - result: `3 passed`
    - artifacts/docs:
      - `novaic-backend/tests/contract/http_probe.py`
      - `novaic-backend/tests/contract/test_runtime_orchestrator_process_startup.py`
  - dependencies:
    - none
  - risk_level: P1

- Task 2: Add CI check preventing unsafe localhost probe usage in targeted test paths.
  - owner: Runtime Team
  - due: 2026-02-24 18:00
  - status: DONE
  - evidence:
    - command: `bash scripts/tools/ci_guard_localhost_probe_safety.sh`
    - result: `localhost probe safety guard passed`
    - artifacts/docs:
      - `novaic-backend/scripts/tools/ci_guard_localhost_probe_safety.sh`
      - `.github/workflows/ci.yml`
  - dependencies:
    - none
  - risk_level: P1

- Task 3: Execute one concurrent stress replay and attach deterministic result summary.
  - owner: Runtime Team
  - due: 2026-02-24 18:00
  - status: DONE
  - evidence:
    - command: `bash scripts/tools/runtime_concurrency_stress_replay.sh 20`
    - result:
      - `runtime_stress_replay_rounds=20`
      - `runtime_stress_replay_passed_rounds=20`
      - `runtime_stress_replay_status=PASS`
    - artifacts/docs:
      - `novaic-backend/scripts/tools/runtime_concurrency_stress_replay.sh`
      - `ops-rounds/round-006/20-reports/runtime-stress-replay.md`
  - dependencies:
    - pytest runtime environment
  - risk_level: P1
