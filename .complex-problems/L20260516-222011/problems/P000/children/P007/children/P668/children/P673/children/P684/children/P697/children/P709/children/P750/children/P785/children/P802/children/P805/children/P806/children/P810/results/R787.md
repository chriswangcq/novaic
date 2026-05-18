# Resource Storage Binary Source Boundary Result

## Summary

Resolved the storage binary source boundary by following Tauri config evidence: packaged desktop resources are sourced from `src-tauri/resources/backends`, so `novaic-storage-a` must exist there. Synchronized the generated `novaic-storage-a` binary into the resource backend directory and verified byte equality.

## Done

- Inspected `novaic-app/src-tauri/tauri.conf.json`, `tauri.ios.conf.json`, and `tauri.android.conf.json`; all map `resources/backends` into packaged `backends`.
- Confirmed `src-tauri/gen/apple/assets/backends/novaic-storage-a` was tracked while `src-tauri/resources/backends/novaic-storage-a` was absent.
- Copied `novaic-storage-a` into `novaic-app/src-tauri/resources/backends/novaic-storage-a`.
- Preserved executable bit and verified the resource binary matches the generated binary byte-for-byte.

## Verification

- `cmp -s novaic-app/src-tauri/resources/backends/novaic-storage-a novaic-app/src-tauri/gen/apple/assets/backends/novaic-storage-a`
- `bash -n novaic-app/src-tauri/resources/backends/start-backends.sh`
- `bash -n novaic-app/src-tauri/gen/apple/assets/backends/start-backends.sh`
- `cmp -s` for both packaged startup script copies.
- `git -C novaic-app check-ignore -v ...` confirmed `novaic-storage-a` is not ignored while historical `novaic-blob-service` is ignored.
- Targeted scans show `novaic-storage-a` is now the packaged startup preference and stale `novaic-blob-service` appears only as fallback/dev-source-repo naming.

## Known Gaps

- The dev source script still refers to the source repo `novaic-blob-service`; this belongs to P807.
- Other source resource backend binaries remain ignored build artifacts; this ticket only resolved the blob/storage binary mismatch that blocked P806.

## Artifacts

- Added `novaic-app/src-tauri/resources/backends/novaic-storage-a`.
