# PR-185A — Rename Device VNC target hook

Status: `[closed]` — 2026-05-03

## Finding

`useDeviceVncTarget` is no longer VNC-specific. It reads a `Device` entity for device-mode UI and keeps an old noVNC-era name.

## Scope

- Rename hook/file/types to `useDeviceTarget`.
- Update import and local variable names in DeviceFloatingPanel.
- Add/update guard so the old hook name stays absent.

## Tests

- App build.
- App unit tests where available.

## Deployment / Git

- Commit/push `novaic-app`.

## Closure

- Renamed `useDeviceVncTarget` to `useDeviceTarget`.
- Updated DeviceFloatingPanel import/local names.
- Added app compatibility guard for the removed old hook file.
- Tests: `npm run test:unit`, `npm run build`.
