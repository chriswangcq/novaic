# PR-197B — App WS Signaling Doc

| Field | Value |
|---|---|
| Status | Done |
| Parent | [PR-197](PR-197-gateway-entangled-boundary-doc-cleanup.md) |
| Repo | docs |

## Task

Rewrite `docs/gateway/app-ws-and-signaling.md` so it says:

- App WS is not the entity data channel.
- App WS pushes Entangled sync endpoint discovery.
- App WS carries WebRTC offer/answer/ICE signaling through Gateway → Business → Device.
- Product entity sync uses direct Entangled WS.

## Tests / Checks

- Grep: no “顺便打包 Entangled Schema 数据包” or “就地数据库插入” in the doc.

## Result

`docs/gateway/app-ws-and-signaling.md` was rewritten around endpoint discovery, push, and WebRTC signaling.
