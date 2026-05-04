# PR-214 Audio Compression Path

| Field | Value |
| --- | --- |
| Status | `[open]` |
| Type | Audio upload efficiency |
| Created | 2026-05-04 |
| Scope | Rust recorder output format, audio Blob metadata, audio tool integration |
| Dependencies | PR-211, PR-212 |

## Goal

Replace normal voice-message WAV/base64 upload with a compressed audio container
while keeping Rust microphone capture as the WKWebView-compatible input path.

## Scope

- Choose and implement a stable compressed output container for the Rust audio
  recorder path.
- Store audio as `blob://audio-input/...` with codec, duration, sample rate,
  channel count, and size metadata.
- Keep Blob Service as byte storage only; no implicit save-time transcode.
- Add explicit transcode/interpretation only if audio QA requires another
  format.

## Acceptance

- Normal voice input no longer uploads WAV/base64.
- Audio metadata is available to Runtime/audio tools.
- Unsupported codec/tool requirements fail explicitly instead of silently
  falling back to WAV.
- Audio QA can consume the compressed BlobRef or an explicitly produced derived
  BlobRef.

## Verification

- Rust recorder tests or focused smoke on macOS.
- App audio upload smoke.
- Runtime audio QA smoke if executor support is present.
- Guard that Blob Service does not implicitly transcode on save.
