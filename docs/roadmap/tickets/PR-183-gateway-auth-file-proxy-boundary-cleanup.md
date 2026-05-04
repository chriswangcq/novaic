# PR-183 — Gateway Auth / File Proxy boundary cleanup

Status: `[closed]` — 2026-05-03

## Goal

Keep Gateway as a narrow Auth/App WS/file proxy boundary. Remove wording and branches that present current product transports as fallback paths, and delete file proxy routes that bypass file metadata ownership.

## Current-State Analysis

- Auth validation has two real token sources:
  - `Authorization: Bearer <jwt>` for REST/WebSocket clients.
  - `X-Original-URI` token extraction for nginx-authenticated browser transports that cannot set custom headers.
- Direct `?token=` on `/internal/auth/validate` is not part of the nginx auth_request contract.
- Product file access now goes through Gateway's auth-bound Blob proxy.
- Direct raw storage-path proxying is a historical bypass and is no longer an
  active product path.

## Small Tickets

- [PR-183A](PR-183A-gateway-auth-token-transport-tightening.md) — tighten auth validation transport wording and remove direct validate query token path.
- [PR-183B](PR-183B-gateway-file-proxy-file-id-boundary.md) — remove raw
  storage-path proxying and pass user boundary explicitly to Blob Service.

## Tests

- Gateway focused tests.
- Full Gateway suite.
- Remote Gateway smoke after deploy.

## Deployment / Git

- Deploy Gateway stack if active Gateway code changes.
- Commit/push `novaic-gateway` and root docs/submodule pointer.

## Closure

- Closed by PR-183A and PR-183B.
- Gateway deployed and remote smoke verified:
  - backend status healthy
  - Gateway root responds 200
  - old raw file path GET with user identity returns 404
