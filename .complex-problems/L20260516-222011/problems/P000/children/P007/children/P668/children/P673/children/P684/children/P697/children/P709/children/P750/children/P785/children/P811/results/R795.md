# Result: Fix VMuse App Sync Script Source Contract

## Summary

Updated `novaic-app/scripts/sync-vmuse-resource.sh` to validate the current VMuse HTTP package contract instead of the removed `src/novaic_mcp_vmuse/main.py` entrypoint, then ran the sync and focused consistency checks.

## Changes

- Replaced the old `main.py` source validation with checks for:
  - `pyproject.toml`
  - `src/novaic_mcp_vmuse/http_server.py`
  - `src/novaic_mcp_vmuse/cli.py`
- Kept the script free of fallback branches for the deleted `main.py` path.
- Ran the script so both app VMuse copies were refreshed from the same source contract:
  - `novaic-app/src-tauri/resources/novaic-mcp-vmuse`
  - `novaic-app/src-tauri/gen/apple/assets/novaic-mcp-vmuse`

## Verification

- `bash -n scripts/sync-vmuse-resource.sh`: passed.
- `./scripts/sync-vmuse-resource.sh`: passed, syncing both resource and generated Apple asset VMuse bundles.
- `rsync --dry-run --itemize-changes` from `../novaic-mcp-vmuse/` to each app VMuse bundle: no output, meaning no pending source-to-bundle drift under the script's exclude rules.
- `diff -qr src-tauri/resources/novaic-mcp-vmuse src-tauri/gen/apple/assets/novaic-mcp-vmuse`: no output, meaning resource and generated copies match.
- Focused scan for stale `src/novaic_mcp_vmuse/main.py`, `main.py`, `FastMCP`, `stdio`, `SSE Endpoint`, `8080/mcp`, and `vmuse_mcp_url` across the sync script and app VMuse bundles: no output.

## Residual Notes

No P811-scoped residual risk remains. The app repository still has many unrelated pre-existing modified files from earlier work; this ticket only touched the VMuse sync script and refreshed VMuse resource/generated bundles through that script.
