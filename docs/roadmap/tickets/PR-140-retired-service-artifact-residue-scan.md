# PR-140 — Retired Service and Packaged Artifact Residue Scan

| Field | Value |
| --- | --- |
| Status | `[scanned]` |
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

- [ ] Add static guardrail in the cleanup follow-up to block retired service names in active startup/config paths.

## Smoke / Deploy

- [x] No deploy for scan-only changes.
- [ ] Cleanup follow-up must run `./deploy status` and affected app/backend smoke.

## Git / Merge

- [ ] Commit ticket updates.
- [ ] Push parent docs update.
