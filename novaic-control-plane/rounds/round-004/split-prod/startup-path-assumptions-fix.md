# Round 004 Startup Path Assumptions Fix

## Target script

- `repos/novaic-gateway/scripts/smoke_gateway_repo_root.sh`
- commit_sha: `282f59fff8747e4b586f6395f65cce1b0a26ca5a`

## Removed monorepo-only assumptions

- removed:
  - `MONOREPO_ROOT="$ROOT_DIR/../../../../../.."`
  - monorepo venv pin: `PYTHON_BIN="$MONOREPO_ROOT/novaic-backend/venv/bin/python3"`
- replaced with split-compatible runtime:
  - `PYTHON_BIN="${PYTHON_BIN:-python3}"`
  - `NOVAIC_SHARED_COMMON_PATH` default to sibling split repo:
    - `$ROOT_DIR/../novaic-shared-runtime-common`

## Migrated paths (source -> target)

- `repos/novaic-gateway/scripts/smoke_gateway_repo_root.sh` (monorepo bootstrap logic) -> `repos/novaic-gateway/scripts/smoke_gateway_repo_root.sh` (split-repo-root bootstrap logic)

## Added startup checks

- starts and validates `runtime-orchestrator`, `gateway`, `tools-server`
- expected markers include:
  - `SPLIT_RUNTIME_HEALTH=PASS`
  - `SPLIT_GATEWAY_HEALTH=PASS`
  - `SPLIT_TOOLS_HEALTH=PASS`
