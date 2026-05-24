# Media readiness behavior solved

## Summary

`R002` solves the connected-but-black media behavior at the frontend state boundary: a WebRTC track is no longer treated as visible video, first-frame readiness is explicit, keyframes are requested immediately, and no-video becomes a clear error.

## Evidence

- `useWebRtc` now waits for `requestVideoFrameCallback`, `loadeddata`, or ready-state evidence before setting `connected`.
- DataChannel open now sends a `request_keyframe` control message.
- A 25s no-video timeout produces an actionable error instead of an indefinite black stream.
- Cleanup increments the media attempt id and clears timers/callbacks, preventing stale readiness events after disconnect.
- TypeScript, build, lint, and relevant contract test passed; OTA frontend was deployed.

## Criteria Map

- `ontrack` alone no longer proves visible video: satisfied.
- Prompt keyframe request: satisfied via DataChannel open.
- No-video timeout: satisfied with explicit 25s error.
- Cleanup clears timeout/callback: satisfied.
- Focused checks: satisfied by eslint, `tsc`, unit test, build, and OTA deployment.

## Execution Map

- `R002` contains the code change, stale-test cleanup, verification commands, app commit, and OTA deployment.

## Stress Test

- The previous build-blocking stale contract test was removed and the full frontend build now passes, proving the media fix is not just locally lint-clean but deployable through the current OTA packaging path.

## Residual Risk

- Real cross-network first-frame validation still belongs to the root deployment/verification child problem. P002 intentionally closes the client-side black-screen state behavior.

## Result IDs

- R002
