# Phase 0 tool surface inventory guardrails implemented

## Summary

Implemented Phase 0 additive guardrails for the shell-boundary migration. No existing Runtime tool behavior was removed. The new policy module classifies the current direct Runtime tool executor surface into final harness primitives and shell-capability migration candidates, and the new tests fail if a future direct executor is added without an explicit target.

## Done

- Added `novaic-agent-runtime/task_queue/tool_surface_policy.py`.
- Added `novaic-agent-runtime/tests/test_tool_surface_boundary.py`.
- Classified final harness primitives as exactly:
  - `shell`
  - `display`
  - `skill_begin`
  - `skill_end`
  - `sleep`
- Classified current non-final direct tools as shell-capability migration candidates:
  - `im_*`
  - `subagent_spawn`
  - `payload_*`
  - `audio_qa`
  - `hd_*`
- Added tests for:
  - every direct `_EXECUTORS` key has a migration target;
  - final harness set is minimal and explicit;
  - current non-final direct tools are shell migration candidates;
  - policy target classes are constrained.

## Verification

- `cd novaic-agent-runtime && python -m pytest tests/test_tool_surface_boundary.py -q`
  - Passed: `4 passed in 0.09s`
- `cd novaic-agent-runtime && python -m pytest tests/test_runtime_tool_path_contract.py tests/test_llm_prompt_contract.py -q`
  - Passed: `10 passed in 0.12s`
- Reviewed git status. The worktree already had unrelated/previous Runtime modifications before this Phase 0 step:
  - `task_queue/handlers/cortex_handlers.py`
  - `task_queue/handlers/tool_handlers.py`
  - `tests/test_pr85_llm_context_smoke_guardrails.py`
  - `tests/test_runtime_tool_path_contract.py`
  - `task_queue/device_tools.py`
  - `tests/unit/task_queue/test_device_tool_handlers.py`
- This Phase 0 step only added:
  - `task_queue/tool_surface_policy.py`
  - `tests/test_tool_surface_boundary.py`

## Known Gaps

- Phase 0 does not yet migrate tools behind shell.
- Phase 0 does not yet introduce `ToolOutputV1`.
- Phase 0 does not remove old direct harness tools; it creates the inventory/guard needed before removal.

## Artifacts

- `novaic-agent-runtime/task_queue/tool_surface_policy.py`
- `novaic-agent-runtime/tests/test_tool_surface_boundary.py`
