# Round 009 Report - Runtime Team

## Implemented Work
- Extended probe-safety guard with warning telemetry: scans all non-allowlisted contract
  tests for localhost probes lacking the shared helper, emits `WARN:` lines and writes a
  machine-readable telemetry report.
- Guard now accepts `PROBE_GUARD_REPORT_PATH` env var to write timestamped telemetry report.
- Replayed startup contract and lifecycle consistency suites after telemetry integration.
- Published final runtime operability runbook for non-author replay.

## Exact Command Evidence + Pass Summary
- `PROBE_GUARD_REPORT_PATH="../ops-rounds/round-009/20-reports/runtime-probe-telemetry.md" bash scripts/tools/ci_guard_localhost_probe_safety.sh`
  - pass summary: `localhost probe safety guard passed (allowlisted=1, checked=1, warnings=0)`
  - telemetry output: `telemetry_report=../ops-rounds/round-009/20-reports/runtime-probe-telemetry.md`
- `pytest -q tests/contract/test_runtime_orchestrator_process_startup.py`
  - pass summary: `3 passed`
- `pytest -q tests/unit/runtime_orchestrator/test_runtime_lifecycle_consistency.py`
  - pass summary: `5 passed`

## Artifact / Doc Paths
- `novaic-backend/scripts/tools/ci_guard_localhost_probe_safety.sh`
- `novaic-backend/tests/contract/http_probe.py`
- `novaic-backend/tests/contract/test_runtime_orchestrator_process_startup.py`
- `novaic-backend/tests/unit/runtime_orchestrator/test_runtime_lifecycle_consistency.py`
- `ops-rounds/round-009/20-reports/runtime-probe-telemetry.md`
- `ops-rounds/round-009/20-reports/runtime-operability-runbook-final.md`
- `ops-rounds/round-009/10-dispatch/team-runtime.md`

## Acceptance Mapping
- Add warning telemetry/report for non-allowlisted localhost probe patterns.
  - status: DONE
  - evidence: guard runs telemetry scan, emits warnings, writes machine-readable report file
- Replay startup and lifecycle suites after telemetry hook.
  - status: DONE
  - evidence: `3 passed` + `5 passed` with fresh timestamps
- Publish final operability runbook for non-author replay.
  - status: DONE
  - evidence: runbook published with step-by-step replay path, expected outputs, and ownership

## Telemetry Summary
- contract_tests_scanned: 6
- allowlisted_tests: 1
- checked_tests: 1
- warnings_count: 0

## Risks / Blockers
- Current blocker: none.
- Residual risk: telemetry is currently report-only; warnings do not yet fail CI.
  Follow-up in next round to decide hard-fail threshold.

## Decision Needed
- issue:
  - Whether to promote telemetry warnings to CI hard-fail in next round.
- options:
  - A) Keep warnings-only mode indefinitely.
  - B) Hard-fail CI if warnings_count > 0 from next round.
  - C) Hard-fail CI if warnings_count > N (configurable threshold).
- recommendation:
  - B. Zero-warning policy from next round enforces long-term hygiene cleanly.
- impact:
  - B: breaks CI immediately if new non-compliant tests are added; gives strong guardrail.
  - C: more lenient but risks gradual drift accumulation.
- owner:
  - Runtime Team + Platform Team
- deadline:
  - 2026-02-26 18:00

## Self Status
- status: DONE
