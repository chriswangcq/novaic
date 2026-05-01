# PR-156C — Add Deploy / Config Overlay Guardrail

| Field | Value |
| --- | --- |
| Status | `[done]` |
| Owner | Codex |
| Parent | [PR-156](PR-156-deploy-config-overlay-residue-review.md) |
| Repos | root scripts/ci, novaic-common |

## Goal

Make the deploy/config boundary fail loud when obsolete deployment paths,
retired env switches, or mirrored overlay logic reappear.

## Scope

- [x] Extend `scripts/ci/check_start_config_contract.py` to check runtime switch
  allowlist and retired file absence.
- [x] Add current-doc/active-code residue checks for old deployment paths.
- [x] Wire the guard into CI.

## Tests / Guardrails

- [x] `python3 scripts/ci/check_start_config_contract.py`
- [x] `./scripts/ci/lint_current_docs_residue.sh`
- [x] `./scripts/ci/lint_retired_service_residue.sh`
- [x] `./scripts/ci/lint_agent_loop_path.sh`
- [x] `python3 -m pytest tests/test_strict_config_runtime_switches_overlay.py tests/test_service_config_runtime_switches.py -q`
- [x] `python3 -m pytest tests/test_pr48_turn_finalizer.py tests/test_runtime_tool_path_contract.py -q`
- [x] Shell syntax check for remaining deploy/start scripts.

## Smoke / Deploy

- [ ] `./deploy status` after PR-156 batch.

## Git

- Commit independently if guardrails pass.
