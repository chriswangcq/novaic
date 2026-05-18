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
User/subagent/system event
  -> Business writes Environment IM event + notification
  -> Business DispatchSubscriber claims dispatchable Environment notifications
  -> DispatchSubscriber builds one canonical Queue dispatch request
  -> Runtime Queue Service starts or buffers the wake session
  -> Runtime builds LLM context through Cortex and executes tools
```

The hot path is Environment notification driven. Chat message type names remain
only as chat projection / IM domain data; they are not a separate wake queue.
Subagent spawn creates the child subagent and delivers the initial task through
Environment IM. Child-to-parent results use the same Environment IM path.

## Dispatch Boundary

Queue dispatch construction is owned by the Business subscriber / Runtime
boundary. Do not rebuild direct service-to-Queue shortcuts in Gateway or App.

Required invariants:

- `agent_id`, `user_id`, `subagent_id`, `message_ids`, and trigger metadata are
  normalized before Runtime sees the request.
- Notification-triggered dispatches use stable idempotency keys derived from the
  Environment notification / source id.
- Direct service-to-Queue dispatch construction is not allowed outside the
  subscriber / queue boundary and its tests.
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

- A user message produces one Environment IM event, one notification, and one Queue dispatch.
- Spawning a child creates a child subagent and an Environment IM initial task.
- A child result sent to the parent is delivered through Environment IM.
- Cortex context shows the active scope expanded and closed scopes folded by
  their `summary.md`.
