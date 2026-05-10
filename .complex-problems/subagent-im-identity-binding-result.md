# SubAgent IM Identity Binding Result

## Summary

Implemented explicit subagent identity binding for outbound shell CLI actions in shared same-agent sandboxes. `agentctl im reply`, `agentctl im send`, and `agentctl subagent spawn` now require `NOVAIC_SUBAGENT_ID` from the current shell execution environment instead of silently falling back to `"agent"` or `"main"`.

## Done

- Added a Cortex shell capability helper that reads the current subagent id from `NOVAIC_SUBAGENT_ID` and fails closed when it is absent or blank.
- Wired `agentctl im reply` and `agentctl im send` to post `sender_subagent_id` from the current shell execution.
- Wired `agentctl subagent spawn` to post `parent_subagent_id` from the current shell execution.
- Hardened the Business internal environment API so IM reply/send requests require an explicit non-blank `sender_subagent_id`.
- Added Runtime shell-output contract coverage proving the bridge injects the current task/subagent id into shell capability env.
- Added Cortex shell tests proving two subagents can reuse the same agent sandbox and still produce distinct outbound identities per exec.
- Added Cortex shell tests proving outbound actions fail without `NOVAIC_SUBAGENT_ID`.
- Added Business API tests proving missing/blank `sender_subagent_id` is rejected and no message is appended.

## Verification

- `PYTHONPATH=.:../novaic-common pytest -q tests/test_shell_capability_runtime.py tests/test_tool_schemas_limits.py` in `novaic-cortex`: 25 passed.
- `PYTHONPATH=.:../novaic-common pytest -q tests/test_environment_internal_api.py tests/test_pr124_subagent_spawn_im.py tests/test_dispatch_subscriber.py` in `novaic-business`: 30 passed.
- `PYTHONPATH=.:../novaic-common pytest -q tests/test_tool_surface_boundary.py tests/test_runtime_tool_path_contract.py tests/unit/task_queue/test_shell_output_contract.py` in `novaic-agent-runtime`: 18 passed.
- Residue scan found no active-code fallback for `NOVAIC_SUBAGENT_ID` to `"agent"` or `"main"`; the only matches are explicit test fixtures using `"main"`.

## Known Gaps

- none

## Artifacts

- `novaic-cortex/novaic_cortex/sandbox.py`
- `novaic-cortex/tests/test_shell_capability_runtime.py`
- `novaic-business/business/internal/environment.py`
- `novaic-business/tests/test_environment_internal_api.py`
- `novaic-agent-runtime/tests/unit/task_queue/test_shell_output_contract.py`
