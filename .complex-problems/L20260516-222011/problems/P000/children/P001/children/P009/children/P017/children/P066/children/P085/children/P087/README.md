# App device WebRTC and UI media residue classification

## Problem

`novaic-app/src` contains device polling fallback logic, software cursor fallback wording, WebRTC RGBA base64 handling, and other browser/device media mechanics. These may be necessary UI mechanics rather than stale compatibility paths, but they need explicit classification.

## Success Criteria

- Inspect device polling, software cursor, WebRTC, and image/media utility hits for fallback/base64/data URL wording.
- Classify each as current browser/device behavior, guard/test fixture, stale residue, or active risk.
- Apply safe comment/name cleanup where wording incorrectly suggests old compatibility behavior.
- Run focused tests or explicit no-code-change verification for touched device/media code.
