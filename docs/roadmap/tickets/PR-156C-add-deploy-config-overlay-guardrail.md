# PR-156C — Add Deploy / Config Overlay Guardrail

| Field | Value |
| --- | --- |
| Status | `[open]` |
| Owner | Codex |
| Parent | [PR-156](PR-156-deploy-config-overlay-residue-review.md) |
| Repos | root scripts/ci, novaic-common |

## Goal

Make the deploy/config boundary fail loud when obsolete deployment paths,
retired env switches, or mirrored overlay logic reappear.

## Scope

- Extend `scripts/ci/check_start_config_contract.py` to check runtime switch
  allowlist and retired file absence.
- Add current-doc/active-code residue checks for old deployment paths.
- Wire the guard into CI.

## Tests / Guardrails

- Run `python3 scripts/ci/check_start_config_contract.py`.
- Run current docs residue lint.
- Run retired service residue lint.

## Smoke / Deploy

- `./deploy status`.

## Git

- Commit independently if guardrails pass.
