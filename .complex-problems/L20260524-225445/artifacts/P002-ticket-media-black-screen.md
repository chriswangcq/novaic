# Make WebRTC media readiness explicit

## Problem Definition

Even after ICE succeeds, the UI can show a connected state before any decoded video frame is visible. This hides media-path failures as a black screen and makes it hard to distinguish signaling/ICE success from actual remote display success.

## Proposed Solution

Trace the media pipeline from frontend `ontrack` through video element playback and DataChannel keyframe request to Rust peer frame writing. Add explicit first-frame readiness handling: the UI should only mark the stream as truly connected after video metadata or first frame is observed, request a keyframe when the control channel opens, and surface a clear error if no frame arrives within a bounded timeout.

## Acceptance Criteria

- The frontend no longer treats `ontrack` alone as proof of visible video.
- A keyframe request is sent promptly once the control DataChannel opens.
- A no-video timeout produces an actionable error instead of an indefinite black screen.
- Cleanup clears any media timeout and does not fire after disconnect.
- Focused lint/type checks cover the modified media code path as far as existing test health allows.

## Verification Plan

Inspect `useWebRtc.ts` and the visual components that consume it. Patch the hook to track first frame readiness with `loadedmetadata`/`requestVideoFrameCallback` fallback behavior. Run eslint on the hook and available TypeScript checks, noting pre-existing unrelated failures.

## Risks

- Browser video APIs differ; `requestVideoFrameCallback` may need a fallback.
- A too-short timeout can mark slow cross-network sessions as failed even though relay eventually works.
- Existing unrelated TypeScript failures may prevent full app build from being green.

## Assumptions

- Rust already writes cached codec config/IDR after connection; frontend should still explicitly request a keyframe to avoid waiting for an encoder cadence.
