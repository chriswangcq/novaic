# Gateway v2 Checklist

This checklist is closed. The current boundary is documented in
[Gateway v2 Current Boundary](../architecture/gateway-v2-target-architecture.md).

## Completed Outcomes

- Queue Service owns dispatch sessions and session buffering.
- Runtime reads and writes entities through the current Business/Entangled path.
- User and subagent messages wake agents through the outbox subscriber path.
- Business dispatch goes through `common.wake.DispatchAssembler`.
- Gateway no longer owns agent wake routing.
- Subagent result delivery is unified as `SUBAGENT_SEND`.

## Current Smoke Checks

- `USER_MESSAGE` creates one outbox item and one dispatch.
- `SUBAGENT_SEND` creates one outbox item and one dispatch.
- Child spawn delivers the initial task as `SUBAGENT_SEND`.
- Parent-directed child result arrives as `SUBAGENT_SEND`.
- Runtime session completion frees the active session and drains buffered
  triggers.
