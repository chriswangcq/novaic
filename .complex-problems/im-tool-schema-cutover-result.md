# IM tool schema cutover result

## Summary

Completed the IM schema cutover for the bounded ticket: direct IM tools are no longer present in the canonical LLM-facing builtin schema, Common metadata no longer tries to derive chat IM tools from that schema, and the ReAct turn finalizer recognizes the new `shell` capability path (`agentctl im reply`) as a reply-only turn closer.

## Done

- Removed IM tools from canonical LLM schema expectations and Common active metadata surfaces:
  - `im_read`
  - `im_reply`
  - `im_send`
  - `im_history`
  - `im_search`
  - `im_context`
- Kept the Environment IM schema module as a non-LLM command contract source for shell capability implementation.
- Updated `shell` guidance to advertise `agentctl im read`, `agentctl im reply --message-file`, `agentctl im history`, and `agentctl im search`.
- Updated `skill_begin` / `skill_end` wording so routine user replies point through shell IM capabilities instead of direct `im_reply`.
- Removed `im_send` from legacy runtime metadata derivation and made `CHAT_TOOLS` empty.
- Updated product semantics so it tracks active LLM-visible tools, not shell-completed IM commands.
- Added `SHELL_CAPABILITY_SCHEMA_CUTOVER_TOOLS` so tests can distinguish completed schema cutover tools from still-direct executors.
- Updated ReAct reply-no-followup detection to treat `shell` calls containing `agentctl im reply` as turn closers.
- Updated no-tool warning contract and tests to steer replies through `agentctl im reply`.

## Verification

- `cd novaic-agent-runtime && python -m pytest tests/test_runtime_tool_path_contract.py tests/test_tool_surface_boundary.py tests/test_pr85_llm_context_smoke_guardrails.py tests/test_pr48_turn_finalizer.py tests/test_llm_prompt_contract.py tests/unit/task_queue/test_environment_tool_handlers.py tests/unit/task_queue/test_shell_output_contract.py -q`
  - Passed: `59 passed`
- `cd novaic-cortex && python -m pytest tests/test_tool_schemas_limits.py tests/test_shell_capability_runtime.py -q`
  - Passed: `14 passed`
- `cd novaic-common && python -m pytest tests/test_tool_definitions_contract.py tests/test_environment_tool_schemas.py tests/test_tool_product_semantics_contract.py tests/test_payload_tool_schemas.py tests/test_llm_assembly_contract.py -q`
  - Passed: `24 passed`

## Residual Risk

- Direct IM executors still exist internally for compatibility and existing unit coverage. This ticket only completes the LLM schema cutover slice; physical executor deletion should be handled by a later cleanup ticket after remaining shell capability migrations are cut over.
- Some tests still use synthetic `im_reply` / `im_read` tool calls to exercise older pure assembly or observation paths. Those are not active LLM schema exposure but should be revisited in the final old-code deletion phase.
