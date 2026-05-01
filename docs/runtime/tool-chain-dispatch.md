# Tool Chain Dispatch

> Current path: `novaic-agent-runtime/task_queue/handlers/tool_handlers.py`.

## Ownership Boundary

Runtime owns dispatch; individual services own execution:

| Tool family | Examples | Execution owner |
| --- | --- | --- |
| User/agent messaging | `chat_reply`, `subagent_spawn`, `subagent_send`, `sleep` | Business internal APIs |
| Cortex scope/workspace | `shell`, `skill_begin`, `skill_end`, `display`, `chat_history`, `audio_qa` | Cortex / Runtime native executors |
| Device actions | VM/desktop/mobile operations | Business → Device → CloudBridge/VmControl |

There is no separate Tools Server, TRS service, or Gateway tool registry in the
current path. Gateway remains a thin edge service; Business is the domain hub;
Cortex owns scope/context/sandbox; Runtime performs the dispatch decision.

## Result Path

Tool results are returned to Runtime and written as Cortex step results. The
LLM sees those structured results in the next context assembly. User-visible
output still requires `chat_reply`.
