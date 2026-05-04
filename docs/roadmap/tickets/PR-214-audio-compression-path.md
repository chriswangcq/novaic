# PR-214 Audio Compression Path

| Field | Value |
| --- | --- |
| Status | `[closed]` |
| Type | Audio upload efficiency |
| Created | 2026-05-04 |
| Scope | Rust recorder output format, audio Blob metadata, audio tool integration |
| Dependencies | PR-211, PR-212 |

## Goal

Replace normal voice-message WAV/base64 upload with a compressed audio container
while keeping Rust microphone capture as the WKWebView-compatible input path.

## Scope

- Implemented AAC/M4A (`audio/mp4`) output for the Rust recorder path on macOS.
- Recorder returns compressed bytes and metadata (`codec`, duration, sample
  rate, channel count, original size, compressed size), not base64.
- Audio messages force multipart Blob upload into `audio-input` and register as
  `voice_messages`.
- Blob Service remains byte storage only; no implicit save-time transcode.
- Unsupported encoder platforms fail explicitly instead of falling back to WAV.

## Acceptance

- Normal voice input no longer uploads WAV/base64.
- Audio metadata is available to Runtime/audio tools.
- Unsupported codec/tool requirements fail explicitly instead of silently
  falling back to WAV.
- Audio QA can consume the compressed BlobRef or an explicitly produced derived
  BlobRef.

## Verification

- `cd novaic-app/src-tauri && cargo check`
- `cd novaic-app && npm run test:unit -- src/application/blobAttachmentPath.test.ts`
- `cd novaic-gateway && PYTHONPATH=.:../novaic-common pytest -q tests/test_pr152_gateway_boundary.py`
- Static guard asserts no recorder `base64_data`, no ChatInput `atob`, and audio
  upload uses `audio-input` / `voice_messages`.
