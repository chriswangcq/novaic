# Gateway v2 - Current Boundary

This document describes the current target boundary. Older Gateway v1/v2
migration notes live in ticket history; they are not the runtime contract.

## Ownership

| Component | Owns | Must Not Own |
|---|---|---|
| Gateway | HTTP edge, auth handoff, sync endpoint discovery | Agent wake orchestration, message lifecycle routing, Cortex scope semantics |
| Entangled | Entity persistence, sync/change delivery, schema registration | Business dispatch decisions, Agent-loop delivery queue |
| Business | Agent/subagent domain APIs, Environment notifications, domain validation, DispatchSubscriber | Queue session execution, Cortex context assembly |
| Runtime Queue Service | Dispatch sessions, wake execution, tool execution, session lifecycle | Entity schema ownership |
| Cortex | LIFO scope tree, context assembly, scope fold via `summary.md` | Business task management, automatic memory inference |

## Wake Path

```text
USER_MESSAGE or SUBAGENT_SEND
  -> Business writes Environment IM event + notification
  -> Business DispatchSubscriber claims the Environment notification
  -> common DispatchAssembler builds one canonical Queue dispatch request
  -> Runtime Queue Service starts or buffers the wake session
  -> Runtime builds LLM context through Cortex and executes tools
```

Only `USER_MESSAGE` and `SUBAGENT_SEND` are message types that directly wake an
agent. Subagent spawn creates the child subagent and delivers the initial task as
a `SUBAGENT_SEND`. Child-to-parent results also use `SUBAGENT_SEND`.

## Dispatch Boundary

All dispatches pass through `common.wake.DispatchAssembler`.

Required invariants:

- `agent_id`, `user_id`, `subagent_id`, `message_ids`, and trigger metadata are
  normalized before Runtime sees the request.
- Message-triggered dispatches use stable idempotency keys derived from the
  message id.
- Direct service-to-Queue dispatch construction is not allowed outside the
  assembler and its tests.
- Health/recovery workers may repair missed dispatches, but they are not the
  normal delivery path.

## Gateway Entangled Dependency

Gateway may use Entangled only for sync endpoint discovery and explicit edge
operations that still belong at the HTTP boundary. Agent wake state, message
routing, and schema-specific behavior must stay in Business/Entangled/Runtime
according to the ownership table above.

## Deleted Paths

The current architecture intentionally has no separate parent-notification
message path, no spawn-specific wake message type, and no report/query/cancel
subagent tool family. Those concepts were removed because they duplicated the
IM path and made agent behavior branchy.

## Smoke Checks

- A user message produces one Environment notification and one Queue dispatch.
- Spawning a child creates a child subagent and a `SUBAGENT_SEND` initial task.
- A child result sent to the parent is delivered as `SUBAGENT_SEND`.
- Cortex context shows the active scope expanded and closed scopes folded by
  their `summary.md`.
