# PR-198B — Overview Dataflow Alignment

| Field | Value |
|---|---|
| Status | Done |
| Parent | [PR-198](PR-198-global-service-topology-doc-cleanup.md) |
| Repo | docs |

## Task

Align `docs/architecture/overview.md` with the current dataflow:

- Gateway provides Entangled sync endpoint discovery, not entity sync itself.
- App connects directly to Entangled WS.
- Business is Entangled HTTP/action owner.
- Runtime calls Cortex/Factory/Business, not Gateway for product state.

## Tests / Checks

- Manual read of topology diagram and bullets.

## Result

`docs/architecture/overview.md` was rewritten as a concise current L1 topology.
