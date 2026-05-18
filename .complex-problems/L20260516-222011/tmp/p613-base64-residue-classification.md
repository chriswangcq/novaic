# P613 Base64/Data URL Classification

## Safe Intentional / Non-Artifact Uses

- `novaic-app/src/components/Chat/VoiceMessageBubble.tsx:50`: tiny `data:audio/wav;base64,...` silent WAV fallback for audio playback. This is audio UI behavior, not image artifact rendering, not tool text.
- `novaic-app/src/hooks/useWebRtc.ts:261-285`: WebRTC remote cursor protocol accepts `rgba_base64`, decodes it to canvas, then creates a cursor `data:image/png` URL for the local cursor overlay. This is real dynamic base64 image handling, but it is device cursor transport/rendering, not BlobRef/artifact display and not shell/tool output text. It is classified as safe intentional non-artifact UI code.

## BlobRef / Authenticated Image Uses

- `novaic-app/src/components/Chat/FileAttachment.tsx`: attachment images render through authenticated image URLs.
- `novaic-app/src/components/Chat/AssistantMessage.tsx`: event images use `AuthenticatedEventImage` and `ImagePreviewOverlay`, not raw base64 tool text.
- `novaic-app/src/components/Visual/SmartValue.tsx`: image preview is limited to `blob://` and HTTP(S) image URLs; it does not treat `data:image` as image preview input.
- `novaic-app/src/application/converters.test.ts` and `novaic-app/src/types/index.ts`: BlobRef metadata/model paths.

## Guard/Test Uses

- `novaic-app/src/application/blobAttachmentPath.test.ts`: asserts attachment/voice paths do not use old base64 upload mechanisms.
- `novaic-app/src/components/Visual/ActivityTimeline.tsx` and test file: raw `data:image/...;base64` / JPEG-like payload detection and redaction guardrails.

## Risky Residue

- No risky UI raw image artifact rendering residue found. The only dynamic `data:image` path is WebRTC cursor rendering, not artifact/tool-output display.
