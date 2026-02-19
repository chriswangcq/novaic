# Round 004 Dispatch - Runtime Team

## Objective
Keep runtime startup reliability green and guard against regression.

## Mandatory Tasks
1. Re-run startup contract suite and lifecycle consistency suite.
2. Add one CI assertion/note to enforce localhost proxy-safe probe pattern.
3. Report any startup flake with exact reproduction steps.

## Acceptance Commands
- `pytest -q tests/contract/test_runtime_orchestrator_process_startup.py`
- `pytest -q tests/unit/runtime_orchestrator/test_runtime_lifecycle_consistency.py`

## Due / Status
- due: 2026-02-23 18:00
- status: DONE_WITH_GAPS

## Execution Tracking
- Task 1: Re-run startup contract suite and lifecycle consistency suite.
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
      - `ops-rounds/round-004/20-reports/team-runtime-report.md`
  - dependencies:
    - none
  - risk_level: P1

- Task 2: Add one CI assertion/note to enforce localhost proxy-safe probe pattern.
  - owner: Runtime Team
  - due: 2026-02-23 18:00
  - status: DONE
  - evidence:
    - docs:
      - `ops-rounds/round-004/20-reports/runtime-ci-proxy-guard-note.md`
      - `novaic-backend/tests/contract/test_runtime_orchestrator_process_startup.py`
  - dependencies:
    - none
  - risk_level: P1

- Task 3: Report any startup flake with exact reproduction steps.
  - owner: Runtime Team
  - due: 2026-02-23 18:00
  - status: DONE_WITH_GAPS
  - evidence:
    - No new flake reproduced in this round's fresh runs.
    - Existing reproduction and signatures:
      - `ops-rounds/round-002/20-reports/runtime-startup-troubleshooting.md`
  - dependencies:
    - environment-level network/proxy variability
  - risk_level: P1
