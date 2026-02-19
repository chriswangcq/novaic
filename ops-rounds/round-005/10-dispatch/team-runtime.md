# Round 005 Dispatch - Runtime Team

## Objective
Turn startup stability from team convention into enforceable regression guardrails.

## Mandatory Tasks
1. Extract proxy-safe localhost probe helper as shared test utility and migrate startup contract tests to it.
2. Add CI check to prevent direct localhost probe patterns without `trust_env=False`.
3. Add one stress replay for concurrent lifecycle contention and report deterministic result.

## Acceptance Commands
- `pytest -q tests/contract/test_runtime_orchestrator_process_startup.py`
- `pytest -q tests/unit/runtime_orchestrator/test_runtime_lifecycle_consistency.py`

## Due / Status
- due: 2026-02-25 18:00
- status: IN_PROGRESS

## Execution Tracking
- Task 1: Extract proxy-safe localhost probe helper as shared test utility and migrate startup contract tests to it.
  - owner: Runtime Team
  - due: 2026-02-25 18:00
  - status: IN_PROGRESS
  - evidence:
    - baseline command: `pytest -q tests/contract/test_runtime_orchestrator_process_startup.py`
    - baseline result: `3 passed`
    - target artifacts:
      - `novaic-backend/tests/contract/test_runtime_orchestrator_process_startup.py`
      - `novaic-backend/tests/test_utils/` (planned shared helper location)
  - dependencies:
    - test utility location convention (cross-team)
  - risk_level: P1

- Task 2: Add CI check to prevent direct localhost probe patterns without `trust_env=False`.
  - owner: Runtime Team
  - due: 2026-02-25 18:00
  - status: PLANNED
  - evidence:
    - target artifact:
      - `ops-rounds/round-005/20-reports/team-runtime-report.md`
  - dependencies:
    - CI check implementation mode decision (lint rule vs script scan)
  - risk_level: P1

- Task 3: Add one stress replay for concurrent lifecycle contention and report deterministic result.
  - owner: Runtime Team
  - due: 2026-02-25 18:00
  - status: PLANNED
  - evidence:
    - baseline command: `pytest -q tests/unit/runtime_orchestrator/test_runtime_lifecycle_consistency.py`
    - baseline result: `5 passed`
  - dependencies:
    - reproducible stress replay approach in current test runtime
  - risk_level: P1
