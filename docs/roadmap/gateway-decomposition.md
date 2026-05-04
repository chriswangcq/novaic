# Gateway Decomposition Archive

Status: archived historical audit.

This page used to describe the 2026-04-10 Gateway decomposition audit. That
snapshot is no longer the current architecture and should not be used as a
roadmap.

Current Gateway boundary is maintained in:

- `docs/architecture/gateway-decomposition-roadmap.md`
- `docs/architecture/gateway-v2-target-architecture.md`
- `docs/architecture/service-topology.md`

Current invariant:

- Gateway owns edge capabilities only: auth, App WebSocket, WebRTC signaling,
  sync endpoint discovery, TURN credentials, and Blob/file proxy.
- Gateway does not own entity schema authority, Agent wake orchestration,
  product message storage, Runtime execution, Cortex scope state, or tool
  registry.
- App business data should flow through Entangled sync/actions into Business,
  then Environment notifications, Queue/Runtime, Cortex, and Entangled activity
  projection.

The old findings about Gateway-hosted message broadcast, internal Agent
orchestration, VM REST paths, and generic entity proxy were useful as
archaeology, but keeping the detailed stale inventory here made it too easy to
mistake an already-closed decomposition problem for the current control flow.
