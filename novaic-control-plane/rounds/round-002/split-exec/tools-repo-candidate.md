# Round 002 Tools Repo Candidate (Tools Team)

## Candidate repo

- target_repo: `novaic-mcp-vmuse`
- objective: extract tools execution stack into independently startable candidate while keeping runtime contracts replayable

## Physical extraction boundaries

| source_path | action | reason |
|---|---|---|
| `novaic-backend/tools_server/**` | EXTRACT | Core tools API/executor/runtime-manager/reliability implementation. |
| `novaic-backend/main_tools.py` | EXTRACT | Tools server process entrypoint and lifecycle wiring. |
| `novaic-backend/scripts/tools/**` | EXTRACT | Probe, policy, and runner-support operational scripts for tools candidate. |
| `novaic-backend/tests/unit/tools_server/**` | EXTRACT | Reliability and contract tests for extracted tools stack. |
| `novaic-backend/tests/unit/common/test_strict_config.py` | SHARE_OR_COPY | Validates shared strict config fields consumed by tools reliability policy. |

## Keep-out boundaries (must not be moved into tools candidate)

| source_path | owner | keep_reason |
|---|---|---|
| `contracts/**` | `novaic-shared-kernel` | Shared contract source of truth across repos. |
| `compatibility.yaml` | `novaic-shared-kernel` | Compatibility matrix remains cross-repo baseline. |
| `novaic-control-plane/**` | `Platform Team` | Round governance and evidence process remain centralized. |

## Candidate operability replay (minimum)

1. `bash scripts/tools/ci_preflight_probe_prereqs.sh`
2. `bash scripts/tools/leak_probe.sh`
3. `pytest -q tests/unit/tools_server/test_api_reliability_controls.py tests/unit/tools_server/test_reliability_policy.py`

Expected markers:
- `[probe-preflight] PASS`
- `[leak-probe] PASS`
- `5 passed`
