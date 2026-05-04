# Message Wake Refactor Status

This roadmap is closed. The current architecture contract is:

- [Message Wake Principles](../architecture/message-wake-principles.md)
- [Gateway v2 Current Boundary](../architecture/gateway-v2-target-architecture.md)

## Current State

- Wake is driven by Environment notifications, not by `chat_messages.lifecycle`
  or `message_outbox`.
- Business creates Environment IM events and notifications from user/subagent/system inputs.
- Business `DispatchSubscriber` claims dispatchable Environment notifications and sends Queue dispatches.
- Runtime Queue Service owns sessions and wake execution.
- Cortex owns LIFO scope state and context assembly.
- Subagent spawn sends the initial task through Environment IM.
- Subagent result delivery uses parent-directed Environment IM.

## Closed Cleanup

- Direct dispatch construction was removed from active Business/Runtime paths.
- Separate subagent report/query/cancel LLM tools were removed.
- Spawn-specific and completion-specific message wake paths were removed.
- Parent notification is not a separate lifecycle route; it is IM.
- Automatic continuity/memory inference is not part of Cortex.
- Message outbox / chat-message lifecycle wake compatibility was removed by the
  Environment notification cutover.

## Current Guardrails

- Tool schema contract tests assert deleted tools are absent.
- Message lifecycle contract tests assert deleted message types are absent.
- Prompt contract tests reject deleted continuity concepts.
- Environment hot-path tests assert notifications are the wake source.
