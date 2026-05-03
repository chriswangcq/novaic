# PR-198 — Global Service Topology Documentation Cleanup

| Field | Value |
|---|---|
| Status | Done |
| Owner | Codex |
| Repos | docs |
| Parent theme | Align global architecture docs with App ↔ Entangled ↔ Business ↔ Runtime reality |

## Problem

Global architecture docs mix current and historical call graphs. Some still show App messages entering through Gateway REST, Workers only calling Business, Gateway as entity proxy, or LLM config owned by Gateway. These docs should present one current topology.

## Small Tickets

- [x] [PR-198A](PR-198A-service-topology-current-flow.md) — Rewrite `docs/architecture/service-topology.md`.
- [x] [PR-198B](PR-198B-overview-dataflow-alignment.md) — Align `docs/architecture/overview.md` with direct Entangled sync and current service calls.
- [x] [PR-198C](PR-198C-app-file-doc-terminology.md) — Fix App/file docs terminology around Gateway HTTP vs Entangled actions.

## Result

Global topology and Entangled boundary docs now share the same current call graph: App direct Entangled sync/action, Business product authority, Subscriber/Queue/Runtime execution, Cortex work trace, Gateway edge only.

## Acceptance

- Global docs share one call graph.
- App message send is documented as Entangled action → Business, not Gateway REST.
- Gateway remaining HTTP responsibilities are explicit and narrow.
- LLM Factory ownership is not attributed to Gateway.
