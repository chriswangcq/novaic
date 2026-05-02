# PR-186E — Cross-Repo Old-Path Residue Guard and Closure

Status: `[closed]` — 2026-05-03

## Analysis

Most old paths are already deleted, but drift tends to return through names, tests, docs, or "temporary" fallback branches.

This ticket closes PR-186 by adding a repo-level guard and updating the ticket index after all acceptance checks pass.

## Scope

- Scan active first-party code for retired main-path terms:
  - wake summary as memory path
  - prompt raw IM replay
  - execution-log user monitor fallback
  - retired direct communication tools
  - message lifecycle / outbox as agent-loop trigger
- Add a guard test or documented static check where useful.
- Mark PR-186 child tickets closed only after targeted tests pass.

## Tests

- Targeted static guards in affected repos.
- Root `git submodule foreach` cleanliness check.

## Deployment / Git

- Commit and push touched subrepos.
- Commit and push parent docs/submodule pointers.

## Closure

- Added `scripts/ci/lint_agent_main_path_acceptance.sh`.
- The guard checks positive ownership markers for Runtime, Business, Cortex, and App, and rejects old prompt/tool/loop/monitor residue in active code.
- Tests:
  - `scripts/ci/lint_agent_main_path_acceptance.sh` → passed
  - `scripts/ci/lint_retired_agent_paths.sh` → passed
  - `scripts/ci/lint_lifecycle_loop_ownership.sh` → passed
- No deploy required; no behavior changed.
