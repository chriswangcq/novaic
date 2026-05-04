# PR-211 Blob Large File / Multipart / Audio Compression Review

| Field | Value |
| --- | --- |
| Status | `[closed]` |
| Type | Blob boundary / roadmap cleanup |
| Created | 2026-05-04 |
| Scope | Blob Service docs, attachment/audio reference, future multipart/audio tickets |
| Dependencies | PR-207 |

## Large Work Order

Reconcile Blob Service documentation with the implemented system and record the
next large-file/multipart/audio-compression work without pretending those paths
already exist.

## State at PR-211 Time

Already true:

- Blob Service is the byte/object-storage boundary.
- Cortex production store uses Blob Service object APIs instead of direct S3.
- Blob refs use `blob://{namespace}/{blob_id}`.
- App attachments then uploaded through Gateway `/api/blobs/from-base64`.
- Audio recording then used Rust `cpal` + WAV + base64 upload.

Missing:

- Multipart upload sessions.
- Direct App/browser upload to object storage.
- Upload presign.
- Resumable upload state.
- Audio compression/transcode path.

Misleading before this ticket:

- `docs/blob-service-architecture.md` described STS, multipart upload, retry,
  and ffmpeg/transcode behavior as if Blob Service already owned them.
- `docs/reference/blob-audio.md` mentioned compression only as a loose future
  note, without a clear target boundary.

## Small Tickets

### PR-211A Current Blob Capability Inventory

- Objective: document what the current Blob implementation actually supports.
- Scope:
  - `docs/reference/blob-service.md`
  - `docs/reference/blob-audio.md`
  - `docs/blob-service-architecture.md`
- Expected result:
  - Current base64/blob/object paths are explicit.
  - Multipart/upload-presign/transcode are explicitly marked not implemented.
- Verification:
  - `rg` current docs for multipart/transcode wording and manual review.

### PR-211B Future Multipart / Audio Work Orders

- Objective: create a durable plan for large files, multipart, and audio
  compression.
- Scope:
  - `docs/roadmap/blob-large-file-multipart-audio.md`
  - `docs/roadmap/tickets/PR-212-blob-multipart-contract-backend.md`
  - `docs/roadmap/tickets/PR-213-app-large-upload-cutover.md`
  - `docs/roadmap/tickets/PR-214-audio-compression-path.md`
  - `docs/roadmap/tickets/PR-215-blob-payload-limits-observability.md`
  - `docs/roadmap/tickets/README.md`
- Expected result:
  - PR-212 through PR-215 exist as future implementation tickets.
  - Future work preserves Blob as byte infrastructure, not business logic.
- Verification:
  - Manual review of work-order sequencing and acceptance criteria.

### PR-211C Docs Index and Boundary Cleanup

- Objective: make the new Blob plan discoverable and remove old overclaiming.
- Scope:
  - `docs/README.md`
  - Blob architecture/reference pages.
- Expected result:
  - The docs index links the Blob plan.
  - Architecture page no longer claims current STS/multipart/ffmpeg ownership.
- Verification:
  - `git diff --check`
  - Docs grep for stale overclaims.

## Result Review

To close this ticket:

- [x] Current Blob capabilities are described as implemented, not aspirational.
- [x] Multipart/direct upload/upload presign/resumable upload are marked as
  future work.
- [x] Audio compression is defined as an explicit future path, not an implicit
  Blob Service side effect.
- [x] Future implementation tickets PR-212..PR-215 are recorded.
- [x] Docs index points to the new plan.

## Verification Log

- `git diff --check`
- `rg -n "STS|MultiPart|multipart|ffmpeg|transcode|压缩|base64|large" docs/blob-service-architecture.md docs/reference/blob-service.md docs/reference/blob-audio.md docs/roadmap/blob-large-file-multipart-audio.md docs/roadmap/tickets/PR-211-blob-large-file-multipart-audio-review.md docs/roadmap/tickets/PR-212-blob-multipart-contract-backend.md docs/roadmap/tickets/PR-213-app-large-upload-cutover.md docs/roadmap/tickets/PR-214-audio-compression-path.md docs/roadmap/tickets/PR-215-blob-payload-limits-observability.md`
- `cd novaic-blob-service && PYTHONPATH=.:../novaic-common pytest -q`
  - Result: `12 passed, 2 skipped`.
- Manual review against:
  - `novaic-blob-service/blob_service/routes.py`
  - `novaic-blob-service/blob_service/backends.py`
  - `novaic-app/src/services/fileUpload.ts`
  - `novaic-app/src-tauri/src/audio_recorder.rs`

## Closure

Closed as a documentation and roadmap reconciliation pass for the state at that
time. PR-212 through PR-216 subsequently implemented multipart, audio
compression, payload limits, and full base64 upload removal. The current active
shape is documented in `docs/reference/blob-service.md` and
`docs/roadmap/blob-large-file-multipart-audio.md`.
