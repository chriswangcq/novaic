# Round 001 Tools Runtime Dependencies (Tools Team)

## Runtime dependency compatibility matrix

| dependency | provider_after_split | tools_usage | compatibility_requirement | replay_check |
|---|---|---|---|---|
| Gateway service (`GATEWAY_URL`) | `API Team` | Builtin tool routes (`memory_*`, `notebook_*`, `chat_*`, quadrant task APIs) and agent tool-config fetch | Internal endpoint contracts and response `success/error` semantics must remain backward compatible | `pytest -q tests/unit/tools_server/test_api_reliability_controls.py` |
| Runtime Orchestrator (`RUNTIME_ORCHESTRATOR_URL`) | `Runtime Team` | Runtime lifecycle and subagent endpoints (`/internal/runtimes*`, `/internal/subagents*`) | Endpoint paths and runtime lifecycle response schema must stay stable for tools executor/runtime manager | `pytest -q tests/unit/tools_server/test_api_reliability_controls.py` |
| VMControl (`VMCONTROL_URL`) | `Desktop Team` + runtime integration owner | VM/Android tool execution proxies (`/api/vmuse/*`, `/api/android/*`, `/api/vms/*`) | VM proxy API contract must preserve success/error payload shape and timeout behavior | `pytest -q tests/unit/tools_server/test_executor_qemu_contract.py` |
| File Service (`FILE_SERVICE_URL`) | `Storage-A/B Team` | `file_pull/file_push`, `mobile_file_pull/mobile_file_push`, display/file-url validation | File URL and upload/download endpoints must remain compatible across tools split | `pytest -q tests/unit/tools_server/test_tool_result_adapter.py tests/unit/tools_server/test_tool_result_format.py` |
| Tool Result Service (`TOOL_RESULT_SERVICE_URL`) | `Storage-A/B Team` | TRS health in `/api/health` and result persistence via SDK call path | TRS availability and create-from-raw flow must remain stable for successful tool responses | `pytest -q tests/unit/tools_server/test_api_reliability_controls.py` |
| Shared tool definitions (`common.tools.definitions`) | `novaic-shared-kernel` | Builtin tool index (`tools_server/tools.py`, `executor.py`) | Tool-name/source alignment and schema compatibility must be versioned and test-gated | `pytest -q tests/unit/tools_server/test_tool_set_alignment.py` |
| Strict config (`config/services.json`, `common.strict_config`) | `Platform Team` or shared infra owner | Reliability policy defaults and env override base values | `tools_reliability` keys and type constraints must remain present and validated | `pytest -q tests/unit/common/test_strict_config.py tests/unit/tools_server/test_reliability_policy.py` |
| Host probe prerequisites (`lsof`, `pgrep`, `python3`) | Tools CI/runtime environment policy | Leak/probe replay scripts in `scripts/tools/*` | Runner OS support policy and script behavior must stay synchronized (Option A) | `bash scripts/tools/ci_preflight_probe_prereqs.sh && bash scripts/tools/leak_probe.sh && pytest -q tests/unit/tools_server/test_policy_doc_sync.py` |

## Baseline reliability replay for this round

1. `bash scripts/tools/ci_preflight_probe_prereqs.sh` -> PASS (`lsof` and `pgrep` resolved).
2. `bash scripts/tools/leak_probe.sh` -> PASS (`fd delta=0`, leaked children empty).
3. `pytest -q tests/unit/tools_server/test_api_reliability_controls.py tests/unit/tools_server/test_reliability_policy.py tests/unit/tools_server/test_policy_doc_sync.py tests/unit/common/test_strict_config.py` -> PASS (`19 passed`).

## Split guardrails

1. Any tools-side dependency contract change must include a consumer impact note in the team report before marking `DONE`.
2. Reliability policy docs and scripts are a synchronized set (`RUNNER_SUPPORT_POLICY.md`, `RELIABILITY_POLICY.md`, `ci_preflight_probe_prereqs.sh`); update together.
3. Post-split CI for tools repo must retain non-author replay commands listed above as required gates.
