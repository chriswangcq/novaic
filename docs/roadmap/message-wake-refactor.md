# Message Wake Refactor Status

This roadmap is closed. The current architecture contract is:

- [Message Wake Principles](../architecture/message-wake-principles.md)
- [Gateway v2 Current Boundary](../architecture/gateway-v2-target-architecture.md)

## Current State

- Wake-eligible chat messages are `USER_MESSAGE` and `SUBAGENT_SEND`.
- Entangled emits outbox items for wake-eligible messages.
- Business `DispatchSubscriber` consumes those items.
- `common.wake.DispatchAssembler` constructs Queue dispatch requests.
- Runtime Queue Service owns sessions and wake execution.
- Cortex owns LIFO scope state and context assembly.
- Subagent spawn sends the initial task through `SUBAGENT_SEND`.
- Subagent result delivery uses parent-directed `SUBAGENT_SEND`.

## Closed Cleanup

- Direct dispatch construction was removed from active Business/Runtime paths.
- Separate subagent report/query/cancel LLM tools were removed.
- Spawn-specific and completion-specific message wake paths were removed.
- Parent notification is not a separate lifecycle route; it is IM.
- Automatic continuity/memory inference is not part of Cortex.

## Current Guardrails

- Tool schema contract tests assert deleted tools are absent.
- Message lifecycle contract tests assert deleted message types are absent.
- Prompt contract tests reject deleted continuity concepts.
- Orphan recovery tests assert only wake-eligible message types surface.
