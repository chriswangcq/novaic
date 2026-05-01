# PR-140 — Retired Service and Packaged Artifact Residue Scan

| Field | Value |
| --- | --- |
| Status | `[deployed]` |
| Owner | Codex |
| Created | 2026-05-01 |
| Repos | parent repo, app, runtime, gateway, deploy scripts |
| Depends on | PR-139 |

## Goal

Find physically retained references to retired services or packaged artifacts that can mislead future work, especially TRS, tools-server, storage-b, Runtime Orchestrator, and old MCP hot paths.

## Scan Plan

1. [x] Search active code and deploy scripts for retired service names.
2. [x] Search packaged assets and generated sidecar paths.
3. [x] Search docs/runbooks separately and classify archaeology vs active instructions.
4. [x] Verify no startup/deploy path still attempts to launch retired services.

## Findings

- High-risk active residue remains in App packaged startup/config paths:
  - `novaic-app/scripts/start-backends.sh` still contains Runtime Orchestrator launch/check logic and passes `--runtime-orchestrator-url`.
  - `novaic-app/src-tauri/resources/backends/start-backends.sh` still attempts to launch `novaic-runtime-orchestrator`.
  - `novaic-app/src-tauri/gen/apple/assets/backends/start-backends.sh` has the same generated packaged residue.
  - `novaic-app/src-tauri/resources/config/services.json` and `novaic-app/src-tauri/gen/apple/assets/config/services.json` still contain `runtime_orchestrator_db_file`, `tools_server`, and `runtime_orchestrator`.
  - `novaic-app/scripts/split/launch_split_only.sh` and `stop_split_only.sh` are still Runtime-Orchestrator centered.
- Runtime residue:
  - `novaic-agent-runtime/main_saga.py` still accepts hidden `--runtime-orchestrator-url`.
  - `novaic-agent-runtime/config/services.schema.json` still mentions `tools_server`.
- Common wording residue:
  - `novaic-common/common/tools/__init__.py` still describes shared definitions for `gateway` and `tools_server`.
- Root `scripts/start.sh` still has a `pkill main_runtime_orchestrator.py` cleanup line.
- No packaged `tools-server`, `storage-b`, or TRS binaries were found in the scanned packaged artifact paths.

## Follow-up Decision

Create a cleanup follow-up for App packaged startup/config plus Runtime hidden arg/schema/docstring cleanup. This is real active residue, not just archaeology.

## Unit / Guardrail Tests

- [x] Added `scripts/ci/lint_retired_service_residue.sh` to block retired service names in active startup/config/runtime paths.
- [x] Wired the guardrail into `.github/workflows/lint.yml`.
- [x] Ran `./scripts/ci/lint_retired_service_residue.sh`.
- [x] Ran shell syntax and JSON validation for touched startup/config artifacts.
- [x] Ran `PYTHONPATH=.:../novaic-common pytest -q tests/test_runtime_tool_path_contract.py tests/test_pr86_execution_log_metadata.py` in `novaic-agent-runtime`.

## Smoke / Deploy

- [x] No deploy for scan-only changes.
- [x] Cleanup follow-up removed Runtime Orchestrator / tools_server active-path residue from app startup/config, runtime CLI schema, common wording, and root stop scripts.

## Git / Merge

- [x] Commit cleanup.
- [x] Push cleanup.

## Closure — 2026-05-01

PR-140 is implemented, committed, pushed, and deployed in the PR-140..PR-146 cleanup batch. Retired Runtime Orchestrator / tools_server names are absent from active startup/config/runtime paths, and CI now guards that invariant.
