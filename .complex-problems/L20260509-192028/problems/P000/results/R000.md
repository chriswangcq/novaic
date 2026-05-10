# Shell CLI Tool Surface Audit Result

## Summary

Completed a read-only audit of the current tool surface against the intended boundary: LLM-facing direct tools should be limited to `shell`, `display`, `skill_begin`, `skill_end`, and `sleep`; interface-like tools should be reachable through shell CLI commands.

The active LLM/runtime path is clean: `AGENT_BUILTIN_TOOL_SCHEMAS` and Runtime `_EXECUTORS` both contain only `display`, `shell`, `skill_begin`, `skill_end`, and `sleep`. The `shell` schema includes the new `desc` field for Agent Monitor display.

The shell CLI substrate covers the policy-listed shell capabilities: IM operations, subagent spawn, audio QA, payload inspection/interpretation, and host desktop device commands. There are still explicit residual items to track: product metadata still includes `subagent_list` and `subagent_history`; `runtimectl` is installed but currently help-only; HD device tests prove `shell-exec` but do not round-trip every HD proxy subcommand.

## Done

- Enumerated active LLM-facing schemas from `common.tools.llm_builtin.AGENT_BUILTIN_TOOL_SCHEMAS`.
- Enumerated Runtime direct executors from `task_queue.handlers.tool_handlers._EXECUTORS`.
- Enumerated Runtime policy shell migration sets from `task_queue.tool_surface_policy`.
- Inspected shell CLI implementation in `novaic_cortex/sandbox.py`.
- Searched for direct-tool residue across `novaic-business`, `novaic-agent-runtime`, `novaic-common`, and `novaic-cortex`.
- Inspected prompt defaults and prompt tests for CLI-oriented guidance.
- Ran targeted guardrail tests across Runtime, Cortex, Common, and Business.

## Evidence

Active LLM schema inventory:

```text
LLM_SCHEMAS= ['shell', 'skill_begin', 'skill_end', 'display', 'sleep']
SHELL_PROPS= ['command', 'desc', 'timeout']
```

Runtime direct executor inventory:

```text
RUNTIME_EXECUTORS= ['display', 'shell', 'skill_begin', 'skill_end', 'sleep']
FINAL_HARNESS_TOOLS= ['display', 'shell', 'skill_begin', 'skill_end', 'sleep']
SHELL_CAPABILITY_SCHEMA_CUTOVER_TOOLS= ['audio_qa', 'hd_clipboard_get', 'hd_clipboard_set', 'hd_file_pull', 'hd_file_push', 'hd_keyboard', 'hd_mouse', 'hd_screenshot', 'hd_shell_exec', 'im_context', 'im_history', 'im_read', 'im_reply', 'im_search', 'im_send', 'payload_qa', 'payload_read', 'payload_search', 'payload_summarize', 'subagent_spawn']
```

Shell CLI implementation evidence:

- `agentctl im read/reply/send/history/search/context` exists in `novaic-cortex/novaic_cortex/sandbox.py`.
- `agentctl subagent spawn` exists.
- `agentctl media audio-qa` exists.
- `cortex payload read/search/summarize/qa` exists.
- `devicectl hd screenshot/mouse/keyboard/shell-exec/clipboard-get/clipboard-set/file-pull/file-push` exists via `_HD_PROXY_PATHS`.
- `/cortex/bin/agentctl`, `/cortex/bin/runtimectl`, `/cortex/bin/cortex`, and `/cortex/bin/devicectl` are installed in sandbox PATH by tests.

Prompt/instruction evidence:

- Business defaults list direct tools as `shell`, `display`, `sleep`, `skill_begin`, and `skill_end`.
- Business defaults direct IM/subagent/audio/payload/device actions through shell commands.
- Prompt tests assert `agentctl im read`, `agentctl im reply`, `agentctl subagent spawn`, and `agentctl im send`, and reject old direct forms such as `im_read(...)`, `im_reply(...)`, and `subagent_spawn(...)`.

Targeted tests run:

```text
novaic-agent-runtime:
20 passed in 0.18s

novaic-cortex:
21 passed in 8.04s

novaic-common:
8 passed in 0.02s

novaic-business:
14 passed in 0.34s
```

## Findings

### Clean Active Path

The active LLM and Runtime execution paths are aligned with the desired boundary. There is no active direct executor for `im_*`, `payload_*`, `audio_qa`, `subagent_spawn`, or `hd_*`. Unknown direct tool names would fail with the small executor registry.

### CLI Coverage

The policy-listed shell capability tools all have a CLI route:

| Capability group | CLI path | Status |
| --- | --- | --- |
| IM read/reply/send/history/search/context | `agentctl im ...` | Covered |
| Subagent spawn | `agentctl subagent spawn` | Covered |
| Audio QA | `agentctl media audio-qa` | Covered |
| Payload read/search/summarize/qa | `cortex payload ...` | Covered |
| HD screenshot/mouse/keyboard/shell/clipboard/file | `devicectl hd ...` | Covered |

### Residuals / Gaps

- `common.tools.definitions.BUILTIN_TOOLS` still exposes product metadata names `subagent_list` and `subagent_history`. They are not LLM schemas and not Runtime executors, but they are still active product metadata and can confuse future maintenance.
- `common.tools.definitions.HD_TOOLS` still contains direct `hd_*` metadata for mounted device capabilities. These are not passed to LLM context, and guard tests cover that, but this remains a metadata-vs-CLI split to keep explicit.
- `runtimectl` is installed as a shell capability command, but currently only exposes help. If runtime diagnostics are intended to move shell-side, this is an unfinished capability surface rather than a migrated feature.
- `novaic-cortex/tests/test_shell_capability_runtime.py` has round-trip coverage for `devicectl hd shell-exec`, but not every HD subcommand. Static implementation covers all `_HD_PROXY_PATHS`; test proof is weaker than the implementation coverage.
- Shell schema/help text advertises the key device commands but does not enumerate `clipboard-set`, `file-pull`, and `file-push` as explicitly as the implementation does.

## Conclusion

For the strict active execution boundary, the migration is correct: the direct tool path is now small and final, and the interface tools that should be shell-side are shell-side.

For “AI-era physical cleanliness”, there are still cleanup candidates: product metadata for subagent list/history, incomplete HD round-trip tests, and the help-only `runtimectl` placeholder. These do not mean the live LLM/Runtime path is using the old tool logic, but they should be tracked if the desired bar is no confusing residue.
