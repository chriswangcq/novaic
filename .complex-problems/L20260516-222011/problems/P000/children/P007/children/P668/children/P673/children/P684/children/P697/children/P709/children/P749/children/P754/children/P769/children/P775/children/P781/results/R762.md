# App BlobRef and artifact preview contract discovery result

## Summary

BlobRef/artifact preview paths are contract-compliant in the inspected App surface. Chat uploads use direct multipart Blob upload and register BlobRef metadata; image/file/audio previews resolve `blob://` through Tauri cache-first commands and browser object URLs. The Rust file command explicitly rejects non-`blob://` references. No active UI path was found that consumes shell stdout media bytes, `tool-output.v1` media payloads, or from-base64/data URL upload paths. The only runtime data URL hit in this slice is a tiny built-in silent WAV used to unlock audio playback, not a transport path.

## Done

- Scanned App frontend and Tauri file commands for BlobRef, artifact, image/file/audio preview, direct bytes, base64, data URL, display, and shell-output terms.
- Inspected `fileUpload.ts`, `file.rs`, `useAuthenticatedImage.ts`, `FileAttachment.tsx`, `ImagePreviewOverlay.tsx`, `VoiceMessageBubble.tsx`, converter tests, and Blob attachment guards.
- Ran focused BlobRef/converter tests.

## Verification

- Scan artifact: `.complex-problems/L20260516-222011/tmp/p781-blob-artifact-preview-scan.txt`.
- `novaic-app/src/services/fileUpload.ts` uses `/api/blobs/upload-config`, direct multipart `/v1/blobs/uploads`, and `/api/blobs/register`, then requires returned references to start with `blob://`.
- `novaic-app/src-tauri/src/commands/file.rs` strips only `blob://`, builds `/blob/v1/blobs/{namespace}/{blob_id}`, and returns an error for non-BlobRef references.
- `useAuthenticatedImage.ts`, `FileAttachment.tsx`, `ImagePreviewOverlay.tsx`, and `VoiceMessageBubble.tsx` fetch cached bytes from `blob://` locators and convert bytes to browser object URLs for UI rendering.
- `blobAttachmentPath.test.ts` guards against `/api/blobs/from-base64`, `/api/files/from-base64`, `FileReader`, `readAsDataURL`, and `base64_data` regressions.
- Focused tests passed: `cd novaic-app && npm run test:unit -- blobAttachmentPath.test.ts converters.test.ts` => 2 files, 6 tests passed.

## Known Gaps

- No BlobRef/artifact preview remediation candidate in this App slice.
- `VoiceMessageBubble.tsx` contains a tiny `data:audio/wav;base64,...` silent WAV for audio context unlocking; classified as a fixed UI fallback, not runtime media transport.
- The unused `SmartValue.tsx` BlobRef/image preview residue is tracked by `P778/R758`, not this active preview path.
- No BlobRef/artifact preview UI files were modified in this discovery child.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p781-blob-artifact-preview-scan.txt`
- Focused `novaic-app` test output.
