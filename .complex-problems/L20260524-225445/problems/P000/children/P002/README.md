# Fix connected-but-black WebRTC media behavior

## Problem

The UI can reach a connected state while the remote video remains black, which means media tracks, keyframe delivery, transceiver direction, codec negotiation, stream attachment, or receiver-side readiness may not be handled correctly once ICE succeeds.

## Success Criteria

- Trace the offer/answer/media pipeline from UI viewer request through Rust WebRTC peer creation to frame capture and video element rendering.
- Identify why a connected peer can produce no visible frames.
- Fix the media path so video track creation, negotiation, and first-frame delivery are explicit and observable.
- Add a timeout/error state that distinguishes signaling connected from video-frame received instead of silently showing black.
- Verify same-LAN behavior remains working while cross-network behavior uses the corrected media path.
