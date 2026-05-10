# IM tool schema cutover success check

## Status

success

## Result IDs

- R000

## Criteria Map

- LLM-visible builtin schemas no longer include direct IM tools: satisfied by `novaic-cortex/tests/test_tool_schemas_limits.py::test_im_tools_are_shell_capabilities_not_llm_schemas`, the Common schema import smoke, and the runtime static schema/executor test excluding `SHELL_CAPABILITY_SCHEMA_CUTOVER_TOOLS`.
- Shell schema/no-tool guidance tells agents to use `agentctl im ...`: satisfied by `novaic-cortex/tests/test_tool_schemas_limits.py::test_shell_schema_names_safety_boundary` and `novaic-agent-runtime/tests/test_llm_prompt_contract.py`.
- Turn-finalizer treats shell `agentctl im reply` as a reply closer: satisfied by new `novaic-agent-runtime/tests/test_pr48_turn_finalizer.py` cases for direct reply, read-then-reply, and finalization with an empty stack.
- Direct IM executors may remain internal but not LLM-visible: satisfied by `SHELL_CAPABILITY_SCHEMA_CUTOVER_TOOLS` policy plus runtime schema/executor guard tests.
- Tests cover schema set, no-tool warning, and shell IM reply finalization: satisfied by the targeted Runtime, Cortex, and Common test batches recorded in R000.

## Execution Map

- Schema source changed in `novaic-common/common/tools/llm_builtin.py`.
- Metadata residue cleaned in `novaic-common/common/tools/definitions.py`.
- Prompt/no-tool guidance updated in `novaic-agent-runtime/task_queue/utils/no_tool_warning.py` and `novaic-common/common/contracts/prompt_fragments.py`.
- Turn-finalizer pure decision changed in `novaic-agent-runtime/task_queue/contracts/react_actions.py` and wrapper comments updated in `novaic-agent-runtime/task_queue/sagas/react_actions.py`.
- Test contracts updated across Runtime, Cortex, and Common.

## Evidence

- Runtime targeted tests: `59 passed`.
- Cortex targeted tests: `14 passed`.
- Common targeted tests: `24 passed`.
- Residual scan found direct IM names only in environment command-contract modules and synthetic legacy/path tests, not as active LLM schema exposure.

## Stress Test

The check intentionally keeps direct environment handler tests in the Runtime batch. That proves the old direct executor implementation still works as internal compatibility, while schema tests prove it is no longer offered to the LLM. The ReAct finalizer test covers the critical behavioral stress case: an LLM sends the actual user reply through `shell`, and the harness still detects the round as reply-only.

## Residual Risk

This solves the IM schema cutover ticket, not the entire tool-boundary migration. Remaining direct payload/subagent/audio/device schema work needs separate tickets. Synthetic tests still mention direct `im_reply` / `im_read` where they test historical context rendering or pure assembly behavior; those are acceptable until the final physical old-code deletion phase.
