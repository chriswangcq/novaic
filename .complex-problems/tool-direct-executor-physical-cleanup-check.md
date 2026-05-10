# Check: Tool Direct Executor Physical Cleanup

## Summary

Success. R000 solves P000: the active Runtime direct executor surface is physically reduced to the final harness set, migrated interface tools are shell capabilities only, and the affected repositories pass full or targeted verification.

## Evidence

- Runtime `_EXECUTORS` inventory is exactly `['display', 'shell', 'skill_begin', 'skill_end', 'sleep']`.
- Direct execution of migrated tool name `im_read` returns the unknown-tool path:
  - `False error Unknown tool: im_read. Available: display, shell, skill_begin, skill_end, sleep`
- LLM builtin schema inventory is exactly `['shell', 'skill_begin', 'skill_end', 'display', 'sleep']`.
- File search found no old executor/schema modules:
  - no `task_queue/handlers/environment_tool_handlers.py`
  - no `task_queue/device_tools.py`
  - no `common/tools/environment.py`
  - no `common/tools/payload.py`
- Residue grep found no active imports of removed direct surfaces:
  - `ENVIRONMENT_EXECUTORS`
  - `DYNAMIC_DEVICE_TOOL_NAMES`
  - `common.tools.environment`
  - `common.tools.payload`

## Criteria Map

- Runtime `_EXECUTORS` contains only final harness tools: satisfied by executor inventory.
- IM, payload, subagent, audio, and device tools are not accepted as direct Runtime executions: satisfied by policy tests, executor inventory, and direct `im_read` unknown-tool probe.
- LLM-facing schemas remain exactly five final harness tools: satisfied by common schema inventory and contract tests.
- Tests assert migrated tool names are shell capabilities only: satisfied by runtime tool surface tests and Cortex shell capability tests.
- Legacy helper code that became unreachable is physically removed where safe: satisfied by deleted runtime/common direct modules and grep evidence.
- Focused Runtime, Cortex, and Common tests pass: exceeded; Runtime/Cortex/Common/Business full or focused suites pass as listed.

## Execution Map

- R000 removed active direct executors and obsolete direct modules.
- R000 moved remaining functionality behind shell capability commands:
  - `agentctl im`
  - `agentctl subagent`
  - `agentctl media audio-qa`
  - `cortex payload`
  - `devicectl hd`
- R000 updated prompt and test contracts so new agent instructions cannot drift back to direct LLM tools.
- R000 fixed test collection hygiene in Common/Business so full package test runs are reproducible from their package roots.

## Stress Test

- `cd novaic-agent-runtime && python -m pytest -q`
  - `588 passed`
- `cd novaic-cortex && python -m pytest -q`
  - `375 passed`
- `cd novaic-common && python -m pytest -q`
  - `136 passed`
- `cd novaic-business && python -m pytest -q`
  - `178 passed`
- Direct migrated-tool probe:
  - `handle_tool_execute(... tool_name="im_read" ...)` returns unknown-tool error.

## Residual Risk

Internal Business `environment_im_*` endpoints and Cortex `payload_*` APIs remain intentionally because shell capability commands require backend APIs. They are not active LLM direct tools and are not Runtime direct executors.

## Result IDs

- R000
