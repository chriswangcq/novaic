# Tool Chain Dispatch

> Current path: `novaic-agent-runtime/task_queue/handlers/tool_handlers.py`.

## Ownership Boundary

Runtime owns dispatch; individual services own execution:

| Tool family | Examples | Execution owner |
| --- | --- | --- |
| User/agent messaging | `shell` running `agentctl im read/reply/send/history/search/context` and `agentctl subagent spawn` | Business Environment/Subagent APIs |
| Cortex scope/workspace | `shell` running `cortex payload ...`, plus direct `skill_begin` / `skill_end` | Cortex / Runtime native executors |
| Local resource inspection | direct `display` / `sleep`, plus `shell` running `agentctl media audio-qa ...` | Runtime native executors |
| Device actions | `shell` running `devicectl hd ...` | Business → Device → CloudBridge/VmControl |

There is no separate Tools Server, external result-store service, or Gateway tool registry in the
current path. Gateway remains a thin edge service; Business is the domain hub;
Cortex owns scope/context/shell orchestration, while sandboxd owns process
execution. Runtime performs the dispatch decision.

## Result Path

Tool results are returned to Runtime and written as Cortex step results. The
LLM sees bounded terminal text or explicit artifact manifests in the next
context assembly. User-visible output is sent from shell with
`agentctl im reply --message-file <path>`.

## Output Contract

Shell is a terminal surface, not a binary or media transport. Runtime projects
shell `stdout` / `stderr` back to the LLM as bounded terminal text, with
truncation diagnostics when needed. Complete raw output remains available from
the durable Cortex step payload and can be inspected through the stable
workspace view, such as `/cortex/ro`, `/cortex/rw`, `$RO`, and `$RW`.

Media-producing CLIs, for example `devicectl hd screenshot`, must return a
`tool-output.v1` artifact manifest. The manifest may include
`blob://runtime-artifact/...` references and concise metadata, but must not
print raw image/audio bytes or base64 payloads into shell text.

`display(blob://...)` is the explicit image perception path. Its public tool
history is text-only summary or placeholder content; image bytes are carried
only through the display perception path into provider-native image content.
Do not rely on display tool text to contain base64, data URLs, or other binary
material.

Stable Cortex file paths are `/cortex/ro` and `/cortex/rw` (or the matching
environment variables). `novaic-cortex-sandbox-*` backing paths are internal
implementation details and must not be copied into docs, prompts, scripts, or
follow-up shell commands.
