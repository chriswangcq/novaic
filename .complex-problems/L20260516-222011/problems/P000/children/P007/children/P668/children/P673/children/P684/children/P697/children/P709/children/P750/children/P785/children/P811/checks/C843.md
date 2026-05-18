# P811 Check: Remove stale VMuse main.py assumption

## Verdict

`success`

## Summary

The follow-up is solved. The app VMuse sync script now validates the current HTTP package contract instead of the removed `main.py` entrypoint, the script ran successfully, and strict one-go rechecks found no stale source validation or bundle drift.

## Criteria Map

- `sync-vmuse-resource.sh` no longer references `src/novaic_mcp_vmuse/main.py`: satisfied by focused `rg` scan returning no output.
- The script validates current VMuse HTTP package files: satisfied by checks for `pyproject.toml`, `http_server.py`, and `cli.py`.
- Resource and generated VMuse copies remain synchronized: satisfied by `diff -qr` returning no output.
- Source-to-bundle drift is clean under the script's exclude rules: satisfied by `rsync --dry-run --itemize-changes` returning no output for both app bundles.
- No stale FastMCP/SSE/stdio/direct-media active-path residue was introduced: satisfied by focused stale-marker `rg` returning no output.

## Evidence

- `bash -n scripts/sync-vmuse-resource.sh`: passed.
- `./scripts/sync-vmuse-resource.sh`: passed and printed both synced bundle paths.
- `git diff --check -- scripts/sync-vmuse-resource.sh src-tauri/resources/novaic-mcp-vmuse src-tauri/gen/apple/assets/novaic-mcp-vmuse`: passed.
- `rsync --dry-run --itemize-changes` from `../novaic-mcp-vmuse/` to both bundle paths: no output.
- `diff -qr src-tauri/resources/novaic-mcp-vmuse src-tauri/gen/apple/assets/novaic-mcp-vmuse`: no output.

## Stress Test

This was a one-go ticket, so the check deliberately tested both the direct edited file and the two generated/resource outputs that the script controls. It also checked for old entrypoint vocabulary and legacy transport markers after executing the script, not only before.

## Residual Risk

No P811-scoped residual risk remains.
