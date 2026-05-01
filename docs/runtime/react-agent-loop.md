# Agent Loop

> Current path: `novaic-agent-runtime/task_queue/sagas/react_think.py`,
> `react_actions.py`, `handlers/llm_handlers.py`, and `handlers/tool_handlers.py`.

## Current Contract

Runtime does not fake tools in prose. The LLM request uses native tool schemas
from the assembled Business/Cortex/common contract, and the returned
`tool_calls` are executed by Runtime.

Reasoning text is preserved separately from user-visible assistant text. The
chat message shown to users comes from `chat_reply`; reasoning and execution
logs are stored for the Agent monitor/debug surfaces.

## Loop Shape

1. Saga opens or reuses the current wake scope through Cortex.
2. Runtime asks Business for the system prompt and Cortex for the current
   scope-tree context.
3. Runtime calls LLM Factory with native tools.
4. Assistant messages and tool calls are written into Cortex steps.
5. Tool calls are dispatched through `tool_handlers`.
6. The loop continues until the LLM closes the current scope with
   `skill_end(report=...)` or reaches an explicit terminal condition.

## Safety

- Queue/Saga serializes work per agent/subagent session.
- Runtime enforces iteration and timeout limits.
- Tool execution results are projected back into Cortex as structured step
  content, then used by the next LLM round.
