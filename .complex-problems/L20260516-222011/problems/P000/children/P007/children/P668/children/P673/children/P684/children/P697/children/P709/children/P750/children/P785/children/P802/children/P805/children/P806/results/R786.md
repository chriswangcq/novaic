# Packaged Blob Binary Startup Alignment Result

## Summary

Aligned the packaged backend startup script copies to the committed storage binary contract. The scripts now prefer `novaic-storage-a`, tolerate the historical `novaic-blob-service` only as a fallback, and emit an explicit diagnostic/log entry when no storage binary is packaged.

## Done

- Updated `novaic-app/src-tauri/resources/backends/start-backends.sh`.
- Updated `novaic-app/src-tauri/gen/apple/assets/backends/start-backends.sh`.
- Added shared `BLOB_SERVICE_BIN` resolution:
  - prefer `$BACKENDS_DIR/novaic-storage-a`
  - fallback to `$BACKENDS_DIR/novaic-blob-service`
  - write `blob-service.log` and stdout diagnostic if neither exists
- Kept the two packaged script copies byte-identical.

## Verification

- `bash -n novaic-app/src-tauri/resources/backends/start-backends.sh`
- `bash -n novaic-app/src-tauri/gen/apple/assets/backends/start-backends.sh`
- `cmp -s novaic-app/src-tauri/resources/backends/start-backends.sh novaic-app/src-tauri/gen/apple/assets/backends/start-backends.sh`
- Targeted scan for `novaic-storage-a`, `novaic-blob-service`, `BLOB_SERVICE_BIN`, and `blob-service.log` confirmed the packaged script references are intentional.

## Known Gaps

- The source resource backend directory still does not contain `novaic-storage-a`; the script now makes that absence explicit instead of silently doing nothing. P809 will do final resource/generated comparison and document any intended binary copy boundary.
- The dev source startup script still references the source repo `novaic-blob-service`; that is outside packaged binary remediation and belongs to the dev startup contract problem.

## Artifacts

- Modified packaged startup scripts listed above.
