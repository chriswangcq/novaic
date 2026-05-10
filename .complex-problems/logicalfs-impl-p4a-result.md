# Direct Blob/Object Usage Audit Result

## Summary

Completed a focused read-only audit for direct Blob/object API usage across Cortex, agent runtime, sandbox service, and nearby architecture/reference docs. The current active Cortex workspace path is no longer directly using Blob object APIs from Workspace/runtime/API code; live `RO` / `RW` access now enters through `CortexLogicalFileAuthority`. The remaining direct Blob/object usages are either allowed byte/artifact paths, transitional persistence adapter internals, tests, or stale documentation/comments that need cleanup.

## Done

- Scanned `novaic-cortex`, `novaic-agent-runtime`, `novaic-sandbox-service`, and relevant `docs/` paths for `BlobCortexStore`, `CortexStore`, `/v1/objects`, `/v1/blobs`, and `blob://`.
- Classified allowed cheap-byte uses:
  - `novaic-cortex/novaic_cortex/blob_payload.py` uses Blob multipart and `blob://cortex-payload/...` for large Cortex payload byte externalization.
  - `novaic-cortex/novaic_cortex/shell_capabilities.py` uses `/v1/blobs/...` only for `agentctl media audio-qa --file-url blob://...`.
  - `novaic-agent-runtime/task_queue/handlers/tool_handlers.py` display handling only accepts `blob://{namespace}/{blob_id}` and fetches bytes from `/v1/blobs/...`.
  - `docs/reference/blob-audio.md` and Blob/audio/tool-output tests document or test cheap Blob byte references.
- Classified transitional/internal persistence adapter uses:
  - `novaic-cortex/novaic_cortex/blob_store.py` contains `BlobCortexStore` and the `/v1/objects` adapter.
  - `novaic-cortex/novaic_cortex/registry.py` still constructs `BlobCortexStore` as the underlying store provider.
  - `novaic-cortex/novaic_cortex/workspace_files.py` is the new narrow live file authority and is the intended place where `CortexStore` remains visible below the boundary.
- Classified stale docs/comments:
  - `novaic-cortex/novaic_cortex/registry.py` still says the registry is "backed by Blob Service" and comments `_stores` as `BlobCortexStore`.
  - `novaic-cortex/novaic_cortex/store.py` still says production uses `BlobCortexStore`.
  - `docs/architecture/cortex.md`, `docs/cortex/object-keys.md`, and `docs/architecture/data-ownership.md` still describe Blob-backed Workspace ownership too broadly.
  - `docs/reference/blob-service.md` and `docs/architecture/logicalfs-realtime-file-authority.md` still mention object APIs; these need wording aligned with the final layering.
- Confirmed the current blocking cleanup work is already represented by child problems P007-P009: add guardrails, clean stale language, then verify the boundary.

## Verification

- Ran focused source scans:
  - `rg -n "BlobCortexStore|/v1/objects|CortexStore|blob://|/v1/blobs" novaic-cortex novaic-agent-runtime novaic-sandbox-service docs/reference docs/architecture docs/cortex`
  - `rg -n "BlobCortexStore|/v1/objects|CortexStore" novaic-cortex/novaic_cortex novaic-sandbox-service`
- Read line-numbered source slices for:
  - `novaic-cortex/novaic_cortex/blob_store.py`
  - `novaic-cortex/novaic_cortex/registry.py`
  - `novaic-cortex/novaic_cortex/workspace_files.py`
- No code was changed by this audit ticket.

## Known Gaps

- P007 still needs code-level guardrails so future live `RO` / `RW` code cannot reintroduce direct Blob/object bypasses.
- P008 still needs stale docs/comments cleaned so future agents do not follow obsolete Blob-backed Workspace wording.
- P009 still needs verification after those cleanup tickets.

## Artifacts

- Audit result file: `.complex-problems/logicalfs-impl-p4a-result.md`
