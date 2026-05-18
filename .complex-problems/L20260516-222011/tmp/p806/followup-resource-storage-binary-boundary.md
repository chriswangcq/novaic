# Resource Storage Binary Source Boundary

## Problem

The packaged startup script now expects `novaic-storage-a`, and generated packaged assets contain that binary, but `novaic-app/src-tauri/resources/backends` does not. Decide and implement the correct source-of-truth boundary so source resources and generated assets no longer accidentally diverge.

## Success Criteria

- Inspect Tauri packaging/resource generation to determine whether `src-tauri/resources/backends` or `src-tauri/gen/apple/assets/backends` is the source of truth for committed backend binaries.
- If resources are the source of truth, add/synchronize `novaic-storage-a` into `src-tauri/resources/backends` and verify generated/resource copies agree as expected.
- If generated assets are intentionally the binary source of truth, add an explicit narrow marker/check that documents this boundary and prevents the resource directory absence from being mistaken for drift.
- Targeted scans and `ls`/`git ls-files` evidence show no accidental `novaic-storage-a`/`novaic-blob-service` mismatch remains.
