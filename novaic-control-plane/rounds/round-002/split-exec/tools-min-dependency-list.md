# Round 002 Tools Minimum Dependency List (Tools Team)

## Runtime must-have dependencies

| dependency | usage in tools candidate | compatibility constraint |
|---|---|---|
| `GATEWAY_URL` | builtin tool routes (`memory_*`, `notebook_*`, `chat_*`, task APIs) | Internal endpoints and `success/error` response contract remain backward compatible. |
| `RUNTIME_ORCHESTRATOR_URL` | runtime lifecycle and subagent routes (`/internal/runtimes*`, `/internal/subagents*`) | Endpoint path + response schema must stay stable for tools executor/runtime manager. |
| `VMCONTROL_URL` | VM/Android tools (`/api/vmuse/*`, `/api/android/*`, `/api/vms/*`) | Preserve proxy payload shape and timeout semantics. |
| `FILE_SERVICE_URL` | file pull/push + display URL validation | File upload/download API and URL shape stay compatible. |
| `TOOL_RESULT_SERVICE_URL` | TRS health and result persistence flow | TRS create/read flow must remain available for successful tool calls. |
| `common.tools.definitions` | builtin tool definition source for `tools_server/tools.py` | Tool names and input schema alignment must be test-gated. |
| `config/services.json` (`tools_reliability`) | timeout/isolation defaults | Keys must exist: `request_timeout_seconds`, `execution_timeout_seconds`, `global_timeout_seconds`, `max_concurrent_per_runtime`. |

## Tooling and host prerequisites

| requirement | purpose | enforcement |
|---|---|---|
| `python3` | run tools server and pytest checks | preflight/probe fail-fast |
| `lsof`, `pgrep` | leak probe fd/process checks | `scripts/tools/ci_preflight_probe_prereqs.sh` + `scripts/tools/leak_probe.sh` |

## Post-split compatibility replay gates

1. `pytest -q tests/unit/tools_server/test_tool_set_alignment.py`
2. `pytest -q tests/unit/tools_server/test_policy_doc_sync.py`
3. `pytest -q tests/unit/common/test_strict_config.py tests/unit/tools_server/test_reliability_policy.py`

Expected markers:
- `1 passed`
- `11 passed`
- `5 passed`
