# Result: Tool Direct Executor Physical Cleanup

## Summary

T000 physically removed migrated direct tool executor residue from the active Runtime/LLM surfaces. IM, payload, subagent, audio, and device operations now route through shell capability commands; Runtime direct executors and canonical LLM builtin schemas are reduced to the final harness set.

## Done

- Runtime `_EXECUTORS` is now limited to final harness tools only:
  - `display`
  - `shell`
  - `skill_begin`
  - `skill_end`
  - `sleep`
- Removed migrated direct executor implementation from `task_queue/handlers/tool_handlers.py`:
  - IM direct executors
  - payload direct executors
  - subagent direct executor
  - audio direct executor
  - dynamic HD/device direct executor
- Deleted obsolete direct executor modules and unit tests:
  - `task_queue/handlers/environment_tool_handlers.py`
  - `task_queue/device_tools.py`
  - runtime environment/payload/device direct-handler tests
  - common environment/payload tool schema modules and tests
- Moved LLM-facing IM, payload, subagent, audio, and device operations behind shell capability commands:
  - `agentctl im ...`
  - `agentctl subagent ...`
  - `agentctl media audio-qa ...`
  - `cortex payload ...`
  - `devicectl hd ...`
- Removed runtime prepare-time dynamic device tool schema merge.
- Updated prompt contracts and tests so user-visible instructions point to shell commands rather than direct tools.
- Updated worker generic substrate tests to assert the current wrapper/factory split instead of stale wrapper implementation details.

## Verification

- Runtime executor inventory:
  - `['display', 'shell', 'skill_begin', 'skill_end', 'sleep']`
- LLM builtin schema inventory:
  - `['shell', 'skill_begin', 'skill_end', 'display', 'sleep']`
- Residue grep:
  - no old direct executor modules found by file search
  - no active imports of `ENVIRONMENT_EXECUTORS`, `DYNAMIC_DEVICE_TOOL_NAMES`, `common.tools.environment`, or `common.tools.payload`
  - remaining `environment_im_*` functions are Business internal HTTP endpoints used by `agentctl`
  - remaining `payload_*` functions are Cortex internal API/bridge methods used by `cortex payload`

## Tests

- `cd novaic-agent-runtime && python -m pytest -q`
  - `588 passed`
- `cd novaic-cortex && python -m pytest -q`
  - `375 passed`
- `cd novaic-common && python -m pytest -q`
  - `136 passed`
- `cd novaic-business && python -m pytest -q`
  - `178 passed`

## Known Gaps

No migrated tool remains as an active LLM direct schema or Runtime direct executor. Internal service endpoints remain because shell capabilities need backend APIs to perform IM, payload, audio, and device operations.

## Artifacts

- `.complex-problems/tool-direct-executor-physical-cleanup-root.md`
- `.complex-problems/tool-direct-executor-physical-cleanup-ticket.md`
- `.complex-problems/tool-direct-executor-physical-cleanup-result.md`
