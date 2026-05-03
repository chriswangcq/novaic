# PR-198A — Service Topology Current Flow

| Field | Value |
|---|---|
| Status | Done |
| Parent | [PR-198](PR-198-global-service-topology-doc-cleanup.md) |
| Repo | docs |

## Task

Rewrite `docs/architecture/service-topology.md` so its service list and message lifecycle match the current system:

- App entity sync via Entangled WS;
- Business handles action hooks and Environment notifications;
- Subscriber dispatches notifications to Queue;
- Runtime workers call Cortex, LLM Factory, Business/Device via tools.

## Tests / Checks

- Grep: no “POST /api/chat/send → Gateway” lifecycle in this doc.

## Result

`docs/architecture/service-topology.md` was rewritten with the current topology and message lifecycle.
