# PR-171D — Repo-wide Retired Path Guardrails

| Field | Value |
| --- | --- |
| Status | `[closed]` |
| Parent | [PR-171](PR-171-final-old-path-physical-deletion.md) |
| Repos | all first-party repos |
| Theme | Regression guard |

## Current-State Analysis

The remaining risk is entropy: old terms can return through source imports, frontend entity contracts, trace projection aliases, or misleading current docs. Historical roadmap tickets may mention old terms, but active source and current runbooks must not.

## Plan

- Add or run source-level guardrails for retired App monitor paths.
- Run existing Runtime/Common/Cortex tool-schema guard tests.
- Update current docs so historical terms are either absent from active-path descriptions or explicitly framed as retired.
- Record the exact guard suite in this ticket.

## Verification Required

- [x] Static guard for retired App monitor source names.
- [x] Runtime/Common schema/executor alignment tests.
- [x] Cortex boundary and projection tests.
- [x] App guard tests.
- [x] Deploy services/frontend after code changes.
- [x] GitHub commit for all changed repos.

## Closure Evidence

- Added `scripts/ci/lint_retired_agent_paths.sh`.
- `bash scripts/ci/lint_retired_agent_paths.sh` → `RETIRED_AGENT_PATHS_LINT=PASS`.
- `bash scripts/ci/lint_cortex_boundary.sh` → `Cortex boundary guard passed.`
- `bash scripts/ci/lint_agent_loop_path.sh` → `AGENT_LOOP_PATH_LINT=PASS`.
- `bash scripts/ci/lint_current_docs_residue.sh` → pass.
- `cd novaic-common && PYTHONPATH=.:../novaic-agent-runtime pytest -q` → 122 passed.
