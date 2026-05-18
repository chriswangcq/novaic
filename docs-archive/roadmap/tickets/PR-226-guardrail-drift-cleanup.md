# PR-226 — Guardrail Drift Cleanup

| Field | Value |
| --- | --- |
| Status | `[closed]` |
| Type | CI guard correctness |
| Created | 2026-05-05 |
| Scope | root CI guard scripts and current Agent Monitor/Activity projection markers |
| Dependencies | PR-193, PR-225 |

## Goal

Make the retired-path and main-path guard scripts describe the current system,
not a previous Activity Timeline implementation. The guards should catch real
regressions without failing on current product code.

## Small Tickets

### PR-226A — Retired Monitor Guard Alignment

- Objective: stop treating the current bottom-capsule participant component as a
  retired monitor path.
- Scope: `scripts/ci/lint_retired_agent_paths.sh`, App monitor naming if needed.
- Expected result: the guard still rejects debug/log monitor paths but does not
  reject current Agent Monitor product components.
- Verification: run the guard and focused App monitor grep.

### PR-226B — Main-path Marker Alignment

- Objective: update main-path acceptance markers from the removed Cortex
  `trace_projection.py` path to the current Runtime materialization and
  Entangled projection path.

## Closure

Closed 2026-05-05. The current component is named `AgentMonitorCapsule`, retired
monitor guards no longer reject it, and main-path acceptance now checks Runtime
activity projection plus Business/App Entangled activity surfaces.
- Scope: `scripts/ci/lint_agent_main_path_acceptance.sh`.
- Expected result: the guard verifies Runtime writes public activity records and
  the App reads Entangled activity entities.
- Verification: run the guard.

## Acceptance

- `scripts/ci/lint_retired_agent_paths.sh` passes.
- `scripts/ci/lint_agent_main_path_acceptance.sh` passes.
- The guards still forbid raw execution-log/result-id/debug payloads from the
  user-facing App monitor path.
