# PR-185 — App Device / VM historical naming cleanup

Status: `[closed]` — 2026-05-03

## Goal

Remove active frontend names/comments that preserve old VNC/listing terminology after the Device/WebRTC/Entangled paths have become the product route.

## Current-State Analysis

- `useDeviceVncTarget` no longer returns a VNC target; it reads a Device entity for device-mode display.
- `useDevices` still exposes `listForUser` and `getDevice` sync helper names for old callers, but active code does not need them.
- The VM Users UI section is active, but its comment says legacy.

## Small Tickets

- [PR-185A](PR-185A-rename-device-vnc-target-hook.md) — rename `useDeviceVncTarget` to `useDeviceTarget`.
- [PR-185B](PR-185B-remove-use-devices-legacy-sync-helpers.md) — remove unused `useDevices` legacy sync helpers and misleading comments.

## Tests

- App build.
- App unit tests where available.

## Deployment / Git

- Commit/push `novaic-app` and root docs/submodule pointer.

## Closure

- Closed by PR-185A and PR-185B.
- App build and unit tests passed.
