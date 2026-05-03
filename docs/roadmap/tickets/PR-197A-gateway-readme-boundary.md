# PR-197A — Gateway README Boundary

| Field | Value |
|---|---|
| Status | Done |
| Parent | [PR-197](PR-197-gateway-entangled-boundary-doc-cleanup.md) |
| Repos | docs, novaic-gateway |

## Task

Update Gateway architecture overview and README language so Gateway is described as edge only:

- Auth/token validation;
- App WS for signaling and push;
- Entangled endpoint discovery;
- file proxy;
- TURN credentials;
- internal auth endpoints.

## Tests / Checks

- Grep docs for Gateway owning all entity CRUD or Entangled schema/action logic.

## Result

Gateway architecture and README text now describe Gateway as edge only.
