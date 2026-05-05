# VmControl Architecture

VmControl is the local runtime inside `novaic-app/src-tauri/vmcontrol`. It owns
desktop/device execution on the user's machine and exposes that execution to the
rest of the system through typed device protocols.

## Current Boundary

```text
App UI
  -> Gateway App WS signaling
  -> Device Service
  -> CloudBridge typed WebSocket
  -> VmControl runtime owner
```

Responsibilities:

- capture and stream desktop/device video through WebRTC;
- forward cursor, keyboard, clipboard, and control events to the local runtime;
- answer Device Service typed CloudBridge commands;
- report local device status back through Device Service.

Non-responsibilities:

- Gateway does not own VmControl runtime state;
- Device Service does not execute local desktop work itself;
- App frontend does not call old local VM HTTP paths for runtime execution.

## Protocol Shape

CloudBridge messages are typed commands/events rather than HTTP-over-WebSocket
payloads. Current protocol details live in
[`docs/gateway/cloudbridge-vm.md`](gateway/cloudbridge-vm.md).

## Related Topics

- [`docs/vmcontrol/webrtc-unification.md`](vmcontrol/webrtc-unification.md)
- [`docs/vmcontrol/h264-hardware-encoding.md`](vmcontrol/h264-hardware-encoding.md)
- [`docs/gateway/cloudbridge-vm.md`](gateway/cloudbridge-vm.md)

