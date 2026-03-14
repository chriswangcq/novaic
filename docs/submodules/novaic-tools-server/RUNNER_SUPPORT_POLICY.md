# Tools Probe Runner Support Policy (Split Repo)

Status: FINAL

## Supported environments
| Environment | Support |
|---|---|
| Ubuntu/Debian CI | YES |
| macOS local dev | YES |
| Non-Linux CI runner | NO |

## Chosen strategy
Option A (fail fast, no fallback).

If dependencies are missing, probe must fail explicitly.

Cross-reference:
- `tools_server/RELIABILITY_POLICY.md`
- `scripts/tools/ci_preflight_probe_prereqs.sh`
