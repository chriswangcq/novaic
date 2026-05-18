# App message media and Blob renderer discovery result

## Summary

Chat/message media rendering was scanned. The primary attachment and markdown image paths use BlobRefs plus Rust cache-first byte fetching, then render local object URLs in the browser. Raw base64/data URL hits in this slice are either test guards, a tiny built-in silent audio fallback, WebRTC cursor rendering, or ActivityTimeline binary-scrubbing logic rather than chat/LLM tool payload leakage. No message/media renderer remediation candidate was found.

## Done

- Discovered relevant message/media files under `novaic-app/src`.
- Inspected chat attachment upload/render paths, markdown image rendering, authenticated image fetching, audio bubble rendering, and attachment contract tests.
- Classified base64/data URL/ObjectURL hits.

## Verification

- Scan artifact: `.complex-problems/L20260516-222011/tmp/p773-message-media-scan.txt`.
- `novaic-app/src/services/fileUpload.ts` requires `blob://` upload results and registers Blob metadata.
- `novaic-app/src/application/blobAttachmentPath.test.ts` asserts chat attachment upload does not use `/from-base64`, `FileReader`, `readAsDataURL`, or `fileToBase64`.
- `novaic-app/src/components/hooks/useAuthenticatedImage.ts` loads bytes through `fetch_cached_bytes` and creates `URL.createObjectURL` without falling back to the raw URL.
- `novaic-app/src/components/Chat/FileAttachment.tsx` uses `useAuthenticatedImage` for image attachments and `get_cached_file` for non-image attachments.
- `novaic-app/src/components/Chat/Markdown.tsx` renders markdown images through `useAuthenticatedImage`.
- `VoiceMessageBubble.tsx` uses `fetch_cached_bytes` for real audio; its `data:audio/wav;base64,...` string is a tiny silent fallback constant, not user/tool media payload propagation.
- `useWebRtc.ts` `rgba_base64`/data URL handling belongs to live cursor rendering, not chat/LLM context.
- `ActivityTimeline.tsx` base64/data-image regexes are used to detect/sanitize binary-looking timeline text.

## Known Gaps

- No remediation candidate in the message/media Blob renderer slice.
- Factory log/raw JSON and shell artifact UI contracts remain open under P774/P775.
- No frontend files were modified in this discovery child.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p773-message-media-scan.txt`
