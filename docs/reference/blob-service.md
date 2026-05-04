# Blob Service Boundary

Blob Service is infrastructure for large byte objects. It is the successor
direction for Storage-A/File Service semantics, but it must not become a new
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

During migration, legacy `fs://` and `/api/files/*` paths may exist only as
explicitly named migration or facade boundaries. New hot paths must write
`blob://...` references. Once a path is migrated, old readers should be
physically deleted and guarded.
