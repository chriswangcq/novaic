# Tool CLI Migration Audit Result

## Summary

The shell capability migration is connected on the live Runtime path.

The active LLM-facing builtin schema source is `novaic-common/common/tools/llm_builtin.py`, and it exposes only:

- `shell`
- `skill_begin`
- `skill_end`
- `display`
- `sleep`

The active Runtime executor registry in `novaic-agent-runtime/task_queue/handlers/tool_handlers.py` matches that same five-tool set. This is guarded by `novaic-agent-runtime/tests/test_runtime_tool_path_contract.py` and `novaic-agent-runtime/tests/test_tool_surface_boundary.py`.

The migrated interface tools are not direct executors and not LLM schemas:

- IM: `im_read`, `im_reply`, `im_send`, `im_history`, `im_search`, `im_context`
- Subagent: `subagent_spawn`
- Audio: `audio_qa`
- Payload inspection: `payload_read`, `payload_search`, `payload_summarize`, `payload_qa`
- Device: `hd_screenshot`, `hd_shell_exec`, `hd_mouse`, `hd_keyboard`, `hd_clipboard_get`, `hd_clipboard_set`, `hd_file_pull`, `hd_file_push`

They are routed through shell capability commands in `novaic-cortex/novaic_cortex/shell_capabilities.py`:

- `agentctl im read/reply/send/history/search/context`
- `agentctl subagent spawn`
- `agentctl media audio-qa`
- `cortex payload read/search/summarize/qa`
- `devicectl hd screenshot/shell-exec/mouse/keyboard/clipboard-get/clipboard-set/file-pull/file-push`

## Done

- `common.tools.llm_builtin.AGENT_BUILTIN_TOOL_SCHEMAS` has only the final five tools and documents shell capability commands.
- `task_queue.handlers.tool_handlers._EXECUTORS` has only the final five tools.
- `task_queue.tool_surface_policy.FINAL_HARNESS_TOOLS` is the same final five-tool set.
- `SHELL_CAPABILITY_SCHEMA_CUTOVER_TOOLS` includes the migrated IM/subagent/audio/payload/device tools and is asserted disjoint from schemas and executors.
- `business/prompt_defaults.py` tells agents to reply through `shell` with `agentctl im reply --message-file`, to read messages with `agentctl im read`, and to use `devicectl`/`cortex payload` inside shell.
- `ReactActions` now treats a shell command containing `agentctl im reply` as the reply/no-follow-up closer.

## Verification

- Inspected `novaic-common/common/tools/llm_builtin.py`.
- Inspected `novaic-agent-runtime/task_queue/handlers/tool_handlers.py`.
- Inspected `novaic-agent-runtime/task_queue/tool_surface_policy.py`.
- Inspected `novaic-cortex/novaic_cortex/shell_capabilities.py`.
- Inspected `novaic-business/business/prompt_defaults.py`.
- Inspected runtime boundary tests that assert migrated tools are disjoint from LLM schemas and direct executors.

## Known Gaps

- `activity_projection.py` still contains display labels for historical direct tool names such as `im_reply`, `payload_read`, `audio_qa`, and `subagent_spawn`. This is projection/compat display logic for old step records, not a live executor or schema path.
- Some old tests still construct historical direct tool calls, especially activity projection and finalizer tests. These are fixture coverage for historical records or guard behavior, not active tool exposure.

## Artifacts

- This result file.
- No code changes were made for this ticket. The audit found no unintegrated live path in the tool CLI migration boundary.
