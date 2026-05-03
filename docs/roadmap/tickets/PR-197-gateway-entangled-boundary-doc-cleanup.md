# PR-197 — Gateway / Entangled Boundary Documentation Cleanup

| Field | Value |
|---|---|
| Status | Done |
| Owner | Codex |
| Repos | docs, novaic-gateway |
| Parent theme | Remove stale Gateway-as-Entangled-host narratives |

## Problem

Several Gateway docs still describe App WS as the entity sync channel, Gateway as inheriting/hosting Entangled, or every entity CRUD path as proxied through Business. The live path is: App connects directly to Entangled sync WS after Gateway endpoint discovery; Gateway only owns auth, App WS signaling/push, file proxy, TURN, and internal auth.

## Small Tickets

- [x] [PR-197A](PR-197A-gateway-readme-boundary.md) — Update `docs/gateway/README.md` and `docs/gateway-architecture.md`.
- [x] [PR-197B](PR-197B-app-ws-signaling-doc.md) — Rewrite `docs/gateway/app-ws-and-signaling.md` around signaling/endpoint discovery only.
- [x] [PR-197C](PR-197C-entangled-hooks-nginx-readme.md) — Update Entangled hook docs and Gateway deployment/readme examples.

## Result

Gateway docs now state App entity sync is direct Entangled WS after Gateway endpoint discovery. App WS docs no longer claim schema/entity sync. Gateway README and Nginx example no longer advertise RemoteEntityStore or unified entity WS.

## Acceptance

- Gateway docs no longer say Gateway is Entangled host/schema/action owner.
- App WS docs explicitly say entity sync is direct Entangled WS, not App WS.
- Gateway README does not advertise Agent/VM business APIs as Gateway-owned.
