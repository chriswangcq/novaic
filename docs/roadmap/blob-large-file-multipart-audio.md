# Blob Large File / Multipart / Audio Compression Plan

Blob is now the byte boundary for Cortex payloads, runtime artifacts, user
attachments, and audio inputs. This page records the current implemented shape
and the next work needed for large files, multipart upload, and audio
compression.

## Current State

Implemented today:

- Blob references use `blob://{namespace}/{blob_id}`.
- `novaic-blob-service` stores bytes and metadata behind Disk or S3-compatible
  backends.
- `/v1/blobs` accepts JSON base64 uploads and returns Blob metadata.
- `/v1/objects` supports raw body object-tree `put/get/list/move/delete` for
  Cortex store files.
- S3-compatible backend uses whole-object `put_object` and GET presign.
- App chat attachments currently go through Gateway `/api/blobs/from-base64`.
- Rust audio recording captures PCM, writes WAV with `hound`, returns base64,
  then the App uploads it as a normal Blob attachment.

Not implemented today:

- Multipart upload sessions.
- Direct browser/App upload to object storage.
- PUT/POST presign for uploads.
- Resumable upload state.
- Server-side audio transcode or compression.
- Automatic payload compression by Blob Service.

## Boundary

Blob Service should remain infrastructure:

- Own byte storage, byte metadata, content hash, tenant boundary, object backend
  selection, and upload lifecycle.
- Not own chat semantics, prompt assembly, Cortex summary semantics, Agent
  Monitor copy, or model-specific audio interpretation.
- Not auto-summarize, auto-compress, or auto-transcode as a hidden side effect.

Compression and multipart are product flows above Blob, using Blob as the byte
store:

- Large file upload: App/Gateway requests an upload session; Blob coordinates
  parts and commit.
- Audio input: App records or encodes a compressed audio container when possible;
  Blob stores the resulting bytes and metadata.
- Explicit processing: any transcode or summarization must be an explicit tool
  or pipeline action that writes a new BlobRef, not a Blob save side effect.

## Target Shape

### Large File / Multipart

The target API should be session-based:

```text
create_upload(namespace, tenant_id, filename, mime_type, size, hash?)
upload_part(session_id, part_number, bytes or presigned part URL)
complete_upload(session_id, ordered_parts, final_hash?)
abort_upload(session_id)
get_upload_status(session_id)
```

Rules:

- Metadata is visible as a stable Blob only after `complete_upload`.
- Incomplete sessions are garbage-collectable.
- Part upload is idempotent by `(session_id, part_number, part_hash)`.
- App must stop base64-encoding large files.
- Gateway may authorize and proxy control-plane calls, but must not become the
  data-plane for large bytes.

### Audio Compression

The target audio path should avoid WAV/base64 for normal voice messages:

```text
Rust recorder → compressed container → Blob upload → audio tool consumes blob://audio-input/...
```

Preferred implementation order:

1. Record compressed audio on the client side where platform support is stable.
2. Store compressed bytes as `blob://audio-input/{blob_id}` with duration,
   codec, sample rate, channel count, and size metadata.
3. Add explicit server-side transcode only when a downstream tool needs a
   different format; output is a new BlobRef.

Blob Service should not decide to transcode by itself.

## Work Orders

### PR-212 Blob Multipart Contract and Backend Support

- Define upload-session schema and lifecycle.
- Add Disk and S3-compatible multipart backend interfaces.
- Add unit tests for create/upload/complete/abort/idempotency.
- Guard that `/v1/blobs` base64 path remains small-file only.

### PR-213 App Large Upload Cutover

- Add App upload strategy that chooses direct/multipart path above a configured
  threshold.
- Remove the TODO-only future branch in `fileUpload.ts` once the new path is
  live.
- Verify large attachments do not pass through base64 or Gateway data-plane.

### PR-214 Audio Compression Path

- Replace normal voice-message WAV/base64 upload with a compressed client-side
  container.
- Preserve Rust microphone path for WKWebView compatibility.
- Record codec/duration/size metadata into Blob.
- Add explicit transcode tool/pipeline only if needed by audio QA.

### PR-215 Blob Payload Limits and Observability

- Add size limits and clear failure semantics for base64 upload, object PUT, and
  multipart session control.
- Add user-facing error copy contracts for too-large payloads.
- Add logs/metrics for upload session lifecycle without leaking raw payload.

## Acceptance

The current system is acceptable only if docs say the truth: base64 and whole
object upload are the implemented path; multipart and audio compression are
future explicit work orders.

Future implementation closes when:

- Large files no longer base64 through App/Gateway.
- Multipart has storage-backed resumable lifecycle and tests.
- Normal voice input is compressed before upload.
- Blob still stores refs and bytes only, with no hidden business interpretation.
