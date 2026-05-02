# PR-185B — Remove useDevices legacy sync helpers

Status: `[closed]` — 2026-05-03

## Finding

`useDevices` exposes `listForUser` and `getDevice` promise wrappers over local store state for old compatibility. Active callers use `devices`, `getGrouped`, or `DeviceService.getDevice` directly.

## Scope

- Remove `listForUser` and `getDevice` from `useDevices`.
- Remove unused destructuring in AgentDrawer.
- Reword VM Users section comment as current UI, not legacy.

## Tests

- App build.
- App unit tests where available.

## Deployment / Git

- Commit/push `novaic-app`.

## Closure

- Removed unused `listForUser` and `getDevice` helpers from `useDevices`.
- Removed unused AgentDrawer destructuring.
- Reworded VM Users comment to describe current UI.
- Added app compatibility guard for removed helper names.
- Tests: `npm run test:unit`, `npm run build`.
