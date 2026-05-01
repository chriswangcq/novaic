# PR-156A — Remove Obsolete Deploy / Start Entrypoints

| Field | Value |
| --- | --- |
| Status | `[done]` |
| Owner | Codex |
| Parent | [PR-156](PR-156-deploy-config-overlay-residue-review.md) |
| Repos | root docs/scripts, novaic-app mirror docs if needed |

## Goal

Physically delete old deployment and startup scripts that no longer represent the
current production path.

## Scope

- Delete obsolete root scripts such as `scripts/start-all.sh`,
  `scripts/deploy-all.sh`, `scripts/deploy-business.sh`,
  `scripts/gateway/deploy-gateway.sh`, and the old subscriber canary helper.
- Delete mirrored obsolete submodule scripts under `scripts/submodules/` where
  they duplicate dead paths.
- Update current runbooks so they point to `./deploy`, server `scripts/start.sh`,
  and `novaic-app/scripts/start-backends.sh`.
- Remove current-doc references to `/opt/novaic/jwt_secret.env` and
  `restart_gw.sh` as active procedures.

## Tests / Guardrails

- [x] `bash -n deploy scripts/start.sh scripts/gateway/deploy-stun.sh scripts/submodules/novaic-app/deploy-frontend.sh novaic-app/scripts/deploy-frontend.sh`
- [x] `./scripts/ci/lint_current_docs_residue.sh`
- [x] `./scripts/ci/lint_agent_loop_path.sh`
- [x] `python3 scripts/ci/check_start_config_contract.py`

## Smoke / Deploy

- [ ] `./deploy status` after the PR-156 batch.
- [x] No service deploy needed for this script/docs-only ticket.

## Git

- Commit independently if tests pass.
