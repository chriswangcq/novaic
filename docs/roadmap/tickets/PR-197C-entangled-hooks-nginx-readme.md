# PR-197C — Entangled Hooks / Nginx / Gateway README Cleanup

| Field | Value |
|---|---|
| Status | Done |
| Parent | [PR-197](PR-197-gateway-entangled-boundary-doc-cleanup.md) |
| Repos | docs, novaic-gateway |

## Task

Remove or rewrite stale language in:

- `docs/gateway/entangled-hooks.md`;
- `novaic-gateway/deploy/nginx-entangled-ws.example.conf`;
- `novaic-gateway/README.md`.

## Tests / Checks

- Grep active docs/source for “Gateway unified WS (entity sync” and “RemoteEntityStore”.

## Result

Entangled hook docs now name Business as action owner. Nginx example uses `/entangled/v1/sync` direct sync and no longer mentions RemoteEntityStore.
