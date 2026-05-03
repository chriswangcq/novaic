# PR-195 — Remove frontend noVNC client residue

Status: `[closed]` — 2026-05-03

## Finding

The app display path no longer embeds the browser noVNC client. `DeviceVNCView`
routes devices through `WebRtcView`, while Rust/VmControl owns the remaining
VNC/RFB protocol work and converts VM frames to WebRTC.

The frontend still carries noVNC-era browser client residue:

- `public/novnc`
- `public/novnc-core`
- `public/vnc.html`
- `public/test-vnc.html`
- `@novnc/novnc`
- `patches/@novnc+novnc+1.5.0.patch`
- Vite alias/comments for `novnc-rfb`
- unused `.vnc-canvas` CSS

## Scope

Remove only the browser noVNC frontend client path.

Do not delete Rust-side VNC/RFB/WebRTC code in `src-tauri/vmcontrol`; that code
is still part of the Linux VM display backend.

## Implementation

- Physically delete noVNC static frontend assets.
- Remove npm dependency and patch-package residue created only for noVNC.
- Remove Vite alias/comment references to noVNC.
- Remove unused CSS targeting noVNC canvas.
- Add/verify guard scan so no frontend noVNC client references remain.

## Tests

- `npm run build`
- `npm run test:unit -- --run`
- Residue scan:
  - frontend noVNC client assets/imports must be absent
  - Rust VNC/RFB protocol references may remain

## Deployment / Git

- Commit `novaic-app`.
- Commit parent repo submodule pointer and this ticket.

## Closure

- [x] Frontend noVNC assets removed.
- [x] `@novnc/novnc` and its patch removed.
- [x] Vite noVNC alias/comments removed.
- [x] App build passes: `npm run build`.
- [x] App unit tests pass: `npm run test:unit -- --run`.
- [x] Residue scan passes for frontend noVNC client path.
- [x] Commits created for app and parent repo.
