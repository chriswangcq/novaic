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
- `/v1/blobs/uploads/*` supports multipart sessions with raw byte parts,
  tenant-scoped status/list/abort/expire, and complete-time Blob metadata.
- `/v1/objects` supports raw body object-tree `put/get/list/move/delete` for
  Cortex store files.
- S3-compatible backend uses whole-object `put_object` and GET presign.
- App chat attachments use Gateway `/api/blobs/upload-config` for control-plane
  setup, direct Blob Service `/v1/blobs/uploads/*` raw part upload through the
  `/blob/` edge, then Gateway `/api/blobs/register` to preserve Business file
  metadata. This applies to small files, large files, and audio inputs.
- Rust audio recording captures PCM, writes a temporary WAV with `hound`, then
  explicitly compresses to AAC/M4A (`audio/mp4`) on macOS and returns compressed
  bytes to the App. Audio messages are uploaded through multipart into
  `blob://audio-input/...`.

Not implemented today:

- Direct browser/App upload to object storage.
- PUT/POST presign for uploads.
- Automatic payload compression by Blob Service.
- Non-macOS compressed encoder path.
- Server-side audio transcode.

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
- App must not base64-encode chat attachments.
- Gateway may authorize and proxy control-plane calls, but must not become the
  data-plane for large bytes.

### Audio Compression

The audio path avoids WAV upload for normal voice messages:

```text
Rust recorder → compressed AAC/M4A container → Blob upload → audio tool consumes blob://audio-input/...
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

- Status: closed.
- Define upload-session schema and lifecycle.
- Store raw byte parts through the configured Blob backend.
- Add unit tests for create/upload/complete/abort/idempotency.
- Historical note: at this point the small-file base64 path still existed; PR-216
  later removed it entirely.

### PR-213 App Large Upload Cutover

- Status: closed.
- App chooses direct/multipart path above the configured threshold.
- Gateway only returns upload config and registers completed BlobRefs.
- Direct multipart bytes pass through the `/blob/` edge to Blob Service, not the
  Gateway application process.
- The TODO-only future branch in `fileUpload.ts` is gone.

### PR-214 Audio Compression Path

- Status: closed.
- Normal voice-message upload now uses a compressed AAC/M4A client-side
  container.
- Rust microphone capture remains the WKWebView-compatible input path.
- The App no longer decodes recorder base64 for voice messages.
- Audio files force multipart upload into `audio-input` and use the
  `voice_messages` product category.
- Unsupported compressed encoder platforms fail explicitly; WAV upload fallback
  is disabled.

### PR-215 Blob Payload Limits and Observability

- Status: closed.
- Added explicit size limits and HTTP `413` failure semantics for object PUT,
  multipart part upload, and completed multipart objects.
- Added documented env knobs for each limit.
- Added lifecycle logs for upload create/part/complete/abort/expire and object
  put without logging raw payload bytes.

## Acceptance

The current system is acceptable only if docs and tests say the truth: all App
chat attachments use multipart raw bytes, voice input is compressed before
upload, and no Gateway/Blob base64 upload API remains in active code.

Future implementation closes when:

- Multipart has storage-backed resumable lifecycle and tests.
- Blob still stores refs and bytes only, with no hidden business interpretation.
