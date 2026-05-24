# WebRTC media readiness made explicit

## Summary

The frontend no longer treats `ontrack` as visible video. It now waits for an actual video frame/readiness signal, requests a keyframe when the control DataChannel opens, and reports a clear no-video error after 25 seconds instead of leaving the user staring at a black stream.

## Done

- Added per-attempt media readiness tracking in `useWebRtc`.
- `ontrack` now attaches the stream and observes video readiness, but does not set `connected`.
- `requestVideoFrameCallback` is used when available; `loadeddata`/ready-state are used as fallback.
- The control DataChannel sends `{ "type": "request_keyframe" }` as soon as it opens.
- A 25s no-video timeout sets an explicit error: `WebRTC connected but no video frame arrived within 25s`.
- Disconnect/unmount clears media readiness timers and cancels pending video frame callbacks.
- Removed stale `src/types/messageContract.test.ts`, which contradicted the current chat-message contract and blocked TypeScript builds.
- Committed and pushed `novaic-app` commit `5cf45ad` (`Make WebRTC video readiness explicit`).
- Deployed frontend OTA v0.3.0 to `https://relay.gradievo.com/resource/frontend/v0.3.0/`.

## Verification

- `npx eslint src/hooks/useWebRtc.ts --max-warnings 0`: passed.
- `npx tsc --noEmit --pretty false`: passed after removing the stale conflicting test.
- `npm run test:unit -- --run src/types/chatMessageContract.test.ts`: passed.
- `npm run build`: passed.
- `./deploy frontend 0.3.0`: passed and uploaded the rebuilt OTA bundle.

## Known Gaps

- This verifies the frontend media state behavior and OTA deployment. A real cross-network session still needs manual/interactive validation from a client outside the LAN.

## Artifacts

- `novaic-app/src/hooks/useWebRtc.ts`
- `novaic-app/src/types/messageContract.test.ts` deleted
- `novaic-app` commit `5cf45ad04...`
- Frontend OTA v0.3.0 deployment
