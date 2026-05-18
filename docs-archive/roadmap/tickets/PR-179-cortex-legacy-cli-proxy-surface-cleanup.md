# PR-179 — Cortex legacy CLI/proxy surface cleanup

Status: `[closed]`

## Problem

Cortex still exposes a legacy Business proxy surface:

- `POST /v1/proxy/{command}` in `novaic_cortex.api`
- `BusinessProxy` in `novaic_cortex.proxy`
- CLI commands such as `chat`, `browser`, `shell_exec`, `qemu`, and `subagent`
- startup wiring through `--business-url`

That makes Cortex look like an owner of chat, device, VM, and SubAgent business behavior. It is no longer true. The active boundary is:

- Cortex owns scope tree, context rendering, workspace, sandbox, and capability JWT.
- Runtime owns LLM tool execution.
- Business owns product mutations and device orchestration.

## Scope

- Physically delete the Cortex Business proxy implementation.
- Remove `/v1/proxy/{command}` and CLI proxy commands.
- Remove Cortex startup dependency on Business URL.
- Update active docs so they do not describe a live proxy surface.
- Add guard tests proving Cortex no longer exposes this path.

## Tests

- Cortex proxy boundary tests.
- Cortex boundary guard tests.
- Full Cortex test suite.
- Static scan for active `BusinessProxy`, `/v1/proxy`, and `--business-url` usage in Cortex/startup.

## Deployment

- Deploy Cortex with the updated startup script.
- Verify `/ready` and service status after restart.

## Git

- Commit and push `novaic-cortex`.
- Commit and push root docs/startup submodule pointer.

## Closure

- Deleted `novaic_cortex.proxy`.
- Removed `/v1/proxy/{command}` from `novaic_cortex.api`.
- Removed proxy CLI commands from `novaic_cortex.cli`; remaining CLI commands are `read`, `write`, `ls`, and `tools`.
- Removed Cortex `--business-url` startup wiring from `main_cortex.py` and `scripts/start.sh`.
- Updated active architecture docs so Cortex no longer claims a BusinessProxy or business proxy role.
- Local tests: `tests/test_pr75_proxy_boundary.py tests/test_pr76_boundary_guard.py` → `9 passed`; full Cortex suite → `400 passed, 16 skipped`.
- Deployment: `./deploy cortex` restarted production backends; remote Cortex `/health` and `/ready` returned ok; old `/v1/proxy/chat` returned `404`.
