# Resolve Resource Storage Binary Source Boundary

## Problem Definition

`novaic-storage-a` exists only in `src-tauri/gen/apple/assets/backends`, while the active packaged startup script is also committed under `src-tauri/resources/backends`. The codebase needs one clear source-of-truth rule so future agents do not keep patching one copy while shipping another.

## Proposed Solution

Inspect Tauri packaging configuration and tracked files to determine which backend asset directory is authoritative. Then either synchronize `novaic-storage-a` into the source resource backend directory, or add an explicit guard/marker that proves generated assets are the intended binary source and prevents accidental drift.

## Acceptance Criteria

- The chosen binary source-of-truth is evidenced by config/file references, not guessed.
- The repository no longer has an unexplained resource/generated disagreement for `novaic-storage-a`.
- The packaged startup script can find `novaic-storage-a` in the source-of-truth packaged asset path or emits a deliberately documented diagnostic in non-binary source paths.
- Targeted scans for `novaic-storage-a`, `novaic-blob-service`, and backend resource paths are clean and understandable.

## Verification Plan

- Inspect `src-tauri/tauri.conf.json`, generated asset config, and backend build/packaging scripts.
- Run `git ls-files` and `ls -l` for resource/generated backend binaries.
- Run targeted `rg` for storage/blob binary names and resource paths.
- Run `bash -n` for packaged startup scripts after any changes.

## Risks

- Copying a 14MB binary may be correct but increases repo duplication; leaving it only in generated assets may be correct but must be explicit.
- Generated directories may be committed artifacts rather than source-of-truth files.

## Assumptions

- No backward compatibility with stale `novaic-blob-service` naming is required beyond an intentional fallback if a packaged artifact still carries that name.
