# Resource Storage Binary Source Boundary Check

## Summary

Success. R787 resolves the boundary with source evidence: Tauri packages `resources/backends`, so `novaic-storage-a` was synchronized into that directory and verified against the generated binary.

## Evidence

- R787 cites `tauri.conf.json`, `tauri.ios.conf.json`, and `tauri.android.conf.json` mapping `resources/backends` to packaged `backends`.
- R787 added `novaic-app/src-tauri/resources/backends/novaic-storage-a`.
- R787 verified byte equality with the generated `novaic-storage-a`.
- R787 verified both packaged startup scripts with `bash -n` and confirmed the script copies remain identical.

## Criteria Map

- Source-of-truth evidenced by config/file references: satisfied by Tauri config resource mapping.
- Repository no longer has unexplained resource/generated disagreement for `novaic-storage-a`: satisfied by adding the resource binary and byte comparing it.
- Packaged startup script can find `novaic-storage-a` in source-of-truth path: satisfied by the resource binary addition plus script preference.
- Targeted scans and `git ls-files`/`check-ignore` evidence are understandable: satisfied by R787 verification.

## Execution Map

- Inspected package config.
- Copied the generated storage binary into the resource backend directory.
- Ran syntax and byte-comparison checks.

## Stress Test

- Checked both desktop and mobile Tauri configs rather than assuming a single config controls all packaged resources.
- Verified `novaic-storage-a` is not ignored, so the new resource binary can be committed.

## Residual Risk

- Other backend binaries in `resources/backends` remain ignored build artifacts; this is not part of P810 because the blocking mismatch was specifically storage/blob.

## Result IDs

- R787
