# Runtime Operability Runbook (Final Handoff)

## Purpose
Provide a non-author replay path for runtime probe governance and lifecycle stability checks.

## Preconditions
- Repository checkout complete.
- Python environment available.
- Execute from `novaic-backend/`.

## Replay Steps

1) Probe safety guard with telemetry output:
- `PROBE_GUARD_REPORT_PATH="../ops-rounds/round-009/20-reports/runtime-probe-telemetry.md" bash scripts/tools/ci_guard_localhost_probe_safety.sh`

2) Startup contract replay:
- `pytest -q tests/contract/test_runtime_orchestrator_process_startup.py`

3) Lifecycle consistency replay:
- `pytest -q tests/unit/runtime_orchestrator/test_runtime_lifecycle_consistency.py`

## Expected Results
- Guard script output includes:
  - `localhost probe safety guard passed (...)`
  - `telemetry_report=.../runtime-probe-telemetry.md`
- Startup contract suite: all tests pass.
- Lifecycle consistency suite: all tests pass.

## Evidence Files (Round 009)
- `ops-rounds/round-009/20-reports/runtime-probe-telemetry.md`
- `ops-rounds/round-009/20-reports/team-runtime-report.md`

## Ownership
- primary owner: Runtime Team
- backup owner: Platform Team

## Review Cadence
- Weekly Friday replay.
- Mandatory replay after any changes to:
  - `tests/contract/http_probe.py`
  - `scripts/tools/ci_guard_localhost_probe_safety.sh`
  - `tests/contract/test_runtime_orchestrator_process_startup.py`
