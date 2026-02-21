# Round 002 Runtime Contract Replay List (Runtime Team)

## Purpose

Define replayable lifecycle/state checks required after physical split so non-authors can verify runtime operability.

## Required replay checks

### 1) Startup and health replay (runtime + gateway wiring baseline)

- command:
  - `cd novaic-backend && bash scripts/smoke_gateway_independent_startup.sh`
- expected_marker:
  - `PASS: runtime-orchestrator healthy on`
  - `PASS: gateway healthy on`

### 2) Runtime startup contract replay

- command:
  - `cd novaic-backend && pytest -q tests/contract/test_runtime_orchestrator_process_startup.py`
- expected_marker:
  - `3 passed`

### 3) Runtime lifecycle consistency replay

- command:
  - `cd novaic-backend && pytest -q tests/unit/runtime_orchestrator/test_runtime_lifecycle_consistency.py`
- expected_marker:
  - `5 passed`

## Contract-critical behaviors under replay

- runtime-orchestrator process becomes healthy within bounded startup window.
- gateway fails fast when runtime orchestrator is unavailable and becomes healthy when available.
- lifecycle idempotency holds for get-or-create and CAS status transitions.
- runtime listing order remains deterministic under tie conditions.

## Consumer impact note

Any change in lifecycle status model or internal health semantics must include explicit consumer impact note for API, Agent Runtime, and Desktop teams in their reports.
