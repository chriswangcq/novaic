# Round 004 Report - Runtime Team

## Completed Work
- Re-ran startup contract suite with fresh evidence and kept it green.
- Re-ran lifecycle consistency suite (including concurrent contention cases) and kept it green.
- Published Round 004 CI proxy-guard note for localhost startup probes.
- Reviewed startup flake status: no new flake observed in this round.

## Command Evidence + Pass Summary
- `pytest -q tests/contract/test_runtime_orchestrator_process_startup.py`
  - result summary: `3 passed`
- `pytest -q tests/unit/runtime_orchestrator/test_runtime_lifecycle_consistency.py`
  - result summary: `5 passed`

## Artifacts / Docs Paths
- `novaic-backend/tests/contract/test_runtime_orchestrator_process_startup.py`
- `novaic-backend/tests/unit/runtime_orchestrator/test_runtime_lifecycle_consistency.py`
- `ops-rounds/round-004/20-reports/runtime-ci-proxy-guard-note.md`
- `ops-rounds/round-004/10-dispatch/team-runtime.md`
- `ops-rounds/round-002/20-reports/runtime-startup-troubleshooting.md`

## Acceptance Mapping
- Re-run startup contract suite and lifecycle consistency suite.
  - status: DONE
  - evidence: two acceptance commands executed, both pass
- Add one CI assertion/note to enforce localhost proxy-safe probe pattern.
  - status: DONE
  - evidence: `runtime-ci-proxy-guard-note.md` + existing `_local_get` helper usage
- Report any startup flake with exact reproduction steps.
  - status: DONE_WITH_GAPS
  - evidence: no new flake in fresh runs; historical reproduction available in troubleshooting doc

## Risks / Blockers
- Current blocker (11:00 sync): none.
- Residual risk: future new startup tests may bypass proxy-safe probe helper and reintroduce env-proxy drift.

## Decision Needed
- issue:
  - Whether to enforce a repository-wide guardrail that forbids direct localhost `httpx.get` probes in startup/contract tests without `trust_env=False`.
- options:
  - A) Keep team convention only (doc + review reminder).
  - B) Add a lightweight static check in CI for startup/contract test files.
  - C) Add a shared helper module and require all startup probes to use it.
- recommendation:
  - C first, then optionally B. A shared helper gives immediate consistency with low maintenance cost.
- impact:
  - Positive: reduces chance of proxy-related false failures and improves CI stability.
  - Cost: small refactor for tests that currently implement ad-hoc probe code.

## Self Status
- status: DONE_WITH_GAPS
