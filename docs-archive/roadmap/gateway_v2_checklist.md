# Gateway v2 Checklist

This checklist is closed. The current boundary is documented in
[Gateway v2 Current Boundary](../architecture/gateway-v2-target-architecture.md).

## Completed Outcomes

- Queue Service owns dispatch sessions and session buffering.
- Runtime reads and writes entities through the current Business/Entangled path.
- User and subagent messages wake agents through Environment notifications.
- Business subscriber dispatches Environment notifications into Queue.
- Gateway no longer owns agent wake routing.
- Subagent result delivery is unified as Environment IM.

## Current Smoke Checks

- User message creates one Environment notification and one dispatch.
- Subagent IM creates one Environment notification and one dispatch.
- Child spawn delivers the initial task as Environment IM.
- Parent-directed child result arrives through Environment IM.
- Runtime session completion frees the active session and drains buffered
  triggers.
