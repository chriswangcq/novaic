# Round 003 Tools Migration Map (Real Split)

## Target split repo

- repo_url: `file:///Users/wangchaoqun/novaic/.split-remotes/novaic-tools-server.git`
- branch: `split-round-003`
- split_commit_sha: `98ca78ddfa098ad893d97e1badf091e408e8d4f1`

## Migrated paths (source -> target)

| source_path | target_path |
|---|---|
| `novaic-backend/tools_server/reliability.py` | `novaic-tools-server/tools_server/reliability.py` |
| `novaic-backend/tools_server/api.py` | `novaic-tools-server/tools_server/api.py` |
| `novaic-backend/tools_server/executor.py` | `novaic-tools-server/tools_server/executor.py` |
| `novaic-backend/tools_server/runtime_manager.py` | `novaic-tools-server/tools_server/runtime_manager.py` |
| `novaic-backend/tools_server/tools.py` | `novaic-tools-server/tools_server/tools.py` |
| `novaic-backend/common/config.py` | `novaic-tools-server/common/config.py` |
| `novaic-backend/common/strict_config.py` | `novaic-tools-server/common/strict_config.py` |
| `novaic-backend/common/http/clients.py` | `novaic-tools-server/common/http/clients.py` |
| `novaic-backend/common/tools/definitions.py` | `novaic-tools-server/common/tools/definitions.py` |
| `novaic-backend/task_queue/utils/trs_sdk.py` | `novaic-tools-server/task_queue/utils/trs_sdk.py` |
| `novaic-backend/scripts/tools/ci_preflight_probe_prereqs.sh` | `novaic-tools-server/scripts/tools/ci_preflight_probe_prereqs.sh` |
| `novaic-backend/scripts/tools/leak_probe.sh` | `novaic-tools-server/scripts/tools/leak_probe.sh` |
| `novaic-backend/tests/unit/tools_server/test_reliability_policy.py` | `novaic-tools-server/tests/unit/tools_server/test_reliability_policy.py` |
| `novaic-backend/tests/unit/tools_server/test_api_reliability_controls.py` | `novaic-tools-server/tests/unit/tools_server/test_api_reliability_controls.py` |

## Runtime dependency contracts

1. `GATEWAY_URL`: internal tools routes and agent config fetch compatibility.
2. `RUNTIME_ORCHESTRATOR_URL`: runtime/subagent lifecycle endpoint compatibility.
3. `VMCONTROL_URL`: VM/Android tool proxy compatibility.
4. `FILE_SERVICE_URL`: file upload/download URL contract compatibility.
5. `TOOL_RESULT_SERVICE_URL`: TRS result persistence compatibility.
6. `tools_reliability` config keys must stay stable across split repos.
