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
- presign/proxy access
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
