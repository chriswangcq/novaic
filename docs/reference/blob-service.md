# Blob Service Boundary

Blob Service is infrastructure for byte and object storage. It owns bytes,
object-tree primitives, and byte-level metadata, but it must not become a new
business center.

## Contract

New large-object references use:

```text
blob://{namespace}/{blob_id}
```

Initial namespaces:

- `user-file` — user uploads and chat attachments.
- `cortex-payload` — large raw payloads referenced by Cortex observations.
- `runtime-artifact` — tool/runtime produced artifacts.
- `audio-input` — audio inputs used by audio tools.

## Blob Service Owns

- byte storage
- object storage primitives: `put`, `get`, `list`, `move_prefix`, `delete`
- infrastructure metadata
- tenant isolation
- direct Blob edge access
- blob lifecycle
- hash-based deduplication

## Blob Service Does Not Own

- chat attachment product meaning
- Cortex scope, step, or summary meaning
- tool observation meaning
- prompt assembly
- memory/profile inference
- Agent Monitor copy

## Service Boundary

Cortex should store semantic work trace:

```json
{
  "observation": {
    "summary": "shell output was long; payload is available behind a ref"
  },
  "payload_ref": "blob://cortex-payload/abc123"
}
```

Business should store product semantics plus a BlobRef, not storage-private URLs.
App should resolve BlobRef through authorized Gateway/Blob access paths and must
not construct object storage URLs directly.

## No Fallback Rule

New hot paths must write `blob://...` references. Historical locator shapes are
detection-only migration inputs; they are not valid runtime APIs and must not be
reintroduced as readers or facades.

## Cortex Object Store

Cortex uses Blob Service object APIs for its `CortexStore` production backend:

```text
tenant_id = {user_id}
namespace = cortex-store
key       = agents/{agent_id}/ro/...
key       = agents/{agent_id}/rw/...
```

Cortex does not own physical OSS/S3 credentials or bucket configuration. Blob
Service decides whether these object keys are backed by OSS/S3 or a local test
backend.

## Large Files and Multipart Status

Current implementation:

- `/v1/blobs/uploads/*` is the Blob Service multipart session API. Parts are raw
  bytes, sessions are tenant-scoped, and stable Blob metadata appears only after
  completion.
- App chat attachments use Gateway `/api/blobs/upload-config` and direct
  `/blob/v1/blobs/uploads/*` raw part upload, then Gateway `/api/blobs/register`
  to create Business file metadata.
- App attachment downloads use the same authenticated `/blob/` edge:
  `/blob/v1/blobs/{namespace}/{blob_id}`. Gateway app does not proxy Blob
  download bytes.
- Payload limits are explicit:
  - object PUT: `NOVAIC_BLOB_MAX_OBJECT_PUT_BYTES` (default 64 MiB)
  - multipart part: `NOVAIC_BLOB_MAX_MULTIPART_PART_BYTES` (default 16 MiB)
  - multipart completed object: `NOVAIC_BLOB_MAX_MULTIPART_COMPLETED_BYTES`
    (default 2 GiB)
  Exceeding these limits returns HTTP `413`; lifecycle logs include ids,
  namespace, tenant, size, and outcome, but not raw bytes.
- `/v1/objects` writes a whole request body. It is for Cortex object-store files,
  not a user-facing resumable upload protocol.
- The S3-compatible backend currently supports whole-object `put_object` and
  Blob edge reads. Upload presign/direct-to-object-storage is not exposed yet.

Target direction:

- Add upload presign/direct-to-object-storage only if App data-plane needs to
  bypass Blob Service HTTP entirely.
- Keep Blob as byte infrastructure; product meaning stays in Business/Cortex/App.
- Do not reintroduce base64 upload APIs. All chat attachment uploads use raw
  multipart bytes, including small files and audio inputs.

See `docs/roadmap/blob-large-file-multipart-audio.md` for the detailed work
orders.
