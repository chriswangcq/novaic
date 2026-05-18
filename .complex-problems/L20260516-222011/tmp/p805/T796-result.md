# App Backend Startup Graph Remediation Result

## Summary

Completed the backend startup graph remediation split. The packaged blob/storage contract now uses `novaic-storage-a`, the app dev script and service config no longer mislabel `19996` as VMControl, stale `vmuse_mcp_url` config was removed, and resource/generated startup scripts/configs were synchronized and verified.

## Done

- P806/R786+R787:
  - packaged startup scripts prefer only `novaic-storage-a`
  - explicit diagnostics remain if storage binary is absent
  - `novaic-storage-a` was synchronized into `src-tauri/resources/backends`
- P807/R788:
  - removed `PORT_CORTEX=19996` from the dev startup script
  - made Cortex an explicit external URL via `NOVAIC_CORTEX_URL` defaulting to `http://127.0.0.1:19996`
  - changed app config `services.vmcontrol` to `services.cortex`
- P808/R789:
  - removed inactive stale `runtime.vmuse_mcp_url`
- P809/R790:
  - rechecked resource/generated scripts, config, and storage binary synchronization
  - removed the stale packaged `novaic-blob-service` fallback

## Verification

- `bash -n` passed for:
  - `novaic-app/scripts/start-backends.sh`
  - `novaic-app/src-tauri/resources/backends/start-backends.sh`
  - `novaic-app/src-tauri/gen/apple/assets/backends/start-backends.sh`
- `python -m json.tool` passed for both app service config copies.
- `cmp -s` passed for:
  - packaged startup script copies
  - service config JSON copies
  - resource/generated `novaic-storage-a`
- `diff -qr` over resource/generated backend directories returned no differences.
- Targeted residue scans for `PORT_CORTEX`, `vmuse_mcp_url`, `8080/mcp`, `$BACKENDS_DIR/novaic-blob-service`, and old packaged blob startup text returned no matches.

## Known Gaps

- `resources/backends/novaic-storage-a` is newly added and currently untracked until final staging.
- Existing historical git tracking policy still ignores three other resource backend binaries while tracking generated binaries; this was made visible but not fully normalized because the blocking storage startup mismatch was the scoped issue.

## Artifacts

- Modified app dev startup script.
- Modified packaged startup script copies.
- Modified service config copies.
- Added resource `novaic-storage-a`.
