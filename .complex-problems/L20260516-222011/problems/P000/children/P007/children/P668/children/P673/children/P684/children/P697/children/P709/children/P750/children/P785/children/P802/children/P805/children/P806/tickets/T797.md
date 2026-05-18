# Packaged Blob Binary Startup Alignment

## Problem Definition

Packaged `start-backends.sh` copies currently check for `novaic-blob-service`, but the committed generated backend assets contain `novaic-storage-a`, and the source resource backend assets do not include either blob binary. This means packaged blob startup silently does nothing or depends on stale binary naming.

## Proposed Solution

Patch the packaged startup script contract so it resolves the committed blob/storage binary explicitly and emits a diagnostic if it is absent. Keep source resource and generated packaged script copies synchronized. If the generated binary is the current intended artifact, align resource expectations to that name rather than preserving the stale `novaic-blob-service` path.

## Acceptance Criteria

- Both packaged startup script copies use the same blob/storage binary resolution logic.
- The logic prefers/uses the committed current binary name and no longer silently skips storage startup without an explicit diagnostic.
- Targeted scans show `novaic-blob-service` references are either removed from packaged scripts or limited to deliberate fallback/diagnostic text.
- `bash -n` passes for both packaged startup scripts.

## Verification Plan

- Run targeted scans for `novaic-blob-service`, `novaic-storage-a`, and `blob-service.log`.
- Run `bash -n` on resource and generated packaged startup scripts.
- Compare the two packaged startup script copies after patching.

## Risks

- The source resource backend directory may intentionally omit large binaries, so the fix should not blindly copy binaries without confirming source-of-truth intent.
- Some deployed package may still contain `novaic-blob-service`; fallback compatibility can be tolerated only if it does not hide the current committed `novaic-storage-a` contract.

## Assumptions

- `novaic-storage-a` is the current committed blob/storage service binary for packaged assets.
- The app should fail loudly in logs when storage cannot start from packaged resources.
