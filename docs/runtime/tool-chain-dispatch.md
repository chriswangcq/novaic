# Tool Chain Dispatch

> Current path: `novaic-agent-runtime/task_queue/handlers/tool_handlers.py`.

## Ownership Boundary

Runtime owns dispatch; individual services own execution:

| Tool family | Examples | Execution owner |
| --- | --- | --- |
| User/agent messaging | `im_reply`, `im_send`, `subagent_spawn` | Business Environment/Subagent APIs |
| Cortex scope/workspace | `shell`, `skill_begin`, `skill_end`, `payload_read`, `payload_search`, `payload_summarize`, `payload_qa` | Cortex / Runtime native executors |
| Local resource inspection | `display`, `audio_qa`, `sleep` | Runtime native executors |
| Device actions | VM/desktop/mobile operations | Business → Device → CloudBridge/VmControl |

There is no separate Tools Server, TRS service, or Gateway tool registry in the
current path. Gateway remains a thin edge service; Business is the domain hub;
Cortex owns scope/context/sandbox; Runtime performs the dispatch decision.

## Result Path

Tool results are returned to Runtime and written as Cortex step results. The
LLM sees those structured results in the next context assembly. User-visible
output requires `im_reply`.
