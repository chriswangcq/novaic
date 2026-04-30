# PR-107 — Close VmControl WebRTC mDNS noise fix

| Field | Value |
| --- | --- |
| **Ticket** | PR-107 |
| **Status** | `[~]` |
| **Scope** | `novaic-app/src-tauri/vmcontrol` |
| **Depends on** | PR-106 |
| **Invariant** | VmControl should use the Gateway STUN/TURN WebRTC path and should not emit repeated macOS mDNS `No route to host` noise during ICE setup. |

## Problem

`webrtc-rs` mDNS candidate resolution can try to send to `0.0.0.0:5353` on macOS, producing repeated `webrtc_mdns::conn: Failed to send mDNS packet No route to host (os error 65)` logs. The product's supported path is Gateway-provided STUN/TURN, not LAN `.local` host-candidate discovery.

## Design

- Disable ICE multicast DNS handling in VmControl's WebRTC `SettingEngine`.
- Keep this as an explicit product policy rather than a hidden fallback.
- Do not refresh `Cargo.lock` in this ticket; the stale lockfile is tracked as a separate optimization item.

## Implementation Checklist

- [x] Configure `SettingEngine` to disable multicast DNS before constructing the WebRTC API.
- [x] Keep the comment clear that STUN/TURN is the supported product path.
- [x] Avoid unrelated `Cargo.lock` churn.

## Unit Test / Compile Work

- [x] Run `cargo check --offline` in `novaic-app/src-tauri/vmcontrol`.
- [x] Verify `Cargo.lock` remains unchanged after compile verification.

## Smoke Test Work

- [x] Run a real Host Desktop WebRTC smoke and confirm frames connect.
- [ ] Run VM/Android WebRTC smoke when those sources are available.
- [x] Confirm Host Desktop runtime logs no longer contain repeated `webrtc_mdns::conn` send errors during setup.

## Deployment Work

- [x] If VmControl is bundled in desktop artifacts, rebuild/reinstall the desktop artifact before declaring production closure.
- [x] If no desktop deployment is performed in this turn, record the remaining delivery step explicitly.

## GitHub / Commit Work

- [x] Commit the VmControl mDNS change as a PR-107-sized change.
- [x] Commit the parent repo submodule pointer in the closure commit.

## Closeout

Implementation and local delivery completed on 2026-04-30; Host Desktop runtime stream smoke passed; Linux VM / Android stream smoke remains open.

Verification:

- `cd novaic-app/src-tauri/vmcontrol && cargo check --offline`
- `./deploy desktop`
- Host Desktop manual smoke via the desktop App Devices view.

Notes:

- `cargo check --offline` succeeds with existing warnings.
- Cargo attempted to refresh the stale lockfile during verification; that generated `Cargo.lock` churn was reverted because lockfile refresh is tracked separately.
- Desktop deploy installed `/Applications/ByClaw.app`.
- Host Desktop smoke evidence included `[WebRTC:HD] Cursor shape detected`, `Broadcaster host_desktop ... -> 1 receivers`, WebRTC cursor forwarding, and VideoToolbox bitrate updates; no `webrtc_mdns::conn` send errors appeared in the observed setup window.
- Teardown produced `DataChannel is not opened` after `webrtc_stop`, which is a disconnect tail event and not the mDNS failure mode tracked by this ticket.
- Remaining runtime smoke: Linux VM / Android WebRTC sessions should be exercised with logs open.
- App commit: `635ce2d fix(vmcontrol): disable mdns ice lookup (PR-107)`.
