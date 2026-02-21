# Round 004 Multi-Repo Bring-Up

## Command

- `bash novaic-control-plane/rounds/round-004/split-prod/bringup_gateway_runtime_tools.sh`

## Expected marker

- `ROUND004_MULTI_REPO_BRINGUP_PASS`

## Bring-up components

- `novaic-gateway` commit: `282f59fff8747e4b586f6395f65cce1b0a26ca5a`
- `novaic-runtime-orchestrator` commit: `b5b1b415883dbe74dc5e4f518dea06a8bbbdae5d`
- `novaic-tools-server` commit: `194bb8b46b7f05181ca7dadc71664b92c0c3f6c3`
- shared package commit: `8b18c023533e7afbdc974a4886af62538c136456`

## Migrated paths (source -> target)

- `novaic-control-plane/rounds/round-003/split-move/repos/novaic-gateway/services/health_routes.py` -> `novaic-control-plane/rounds/round-003/split-move/repos/novaic-shared-runtime-common/shared_runtime_common/service_runtime.py`
- `novaic-control-plane/rounds/round-003/split-move/repos/novaic-runtime-orchestrator/runtime_orchestrator/main.py` -> shared import path to `shared_runtime_common`
- `novaic-control-plane/rounds/round-003/split-move/repos/novaic-tools-server/tools_server/main.py` -> shared import path to `shared_runtime_common`
