# WebRTC Unified Screen Pipeline

VmControl exposes device and desktop video through one WebRTC media pipeline.
The active product surface does not branch by display protocol in the frontend.

## Current Pipeline

```text
source frame producer
  -> encoder / packetizer
  -> WebRTC media track
  -> App video renderer
```

Frame producers can be local desktop capture, Android screen capture, or other
device-specific capture implementations. They are normalized before reaching
the App UI.

## Input Channel

Keyboard, pointer, clipboard, and control events travel through the WebRTC data
channel or the typed CloudBridge path owned by VmControl/Device Service. The App
does not maintain per-device retired display protocols.

## Ownership

- VmControl owns capture, encoding, and input injection.
- Device Service owns device routing and CloudBridge command brokering.
- Gateway owns App-facing signaling and TURN credentials.
- App renders the current device stream and sends user input intents.
