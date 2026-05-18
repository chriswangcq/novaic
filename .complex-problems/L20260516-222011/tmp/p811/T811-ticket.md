# Ticket: Fix VMuse App Sync Script Source Contract

## Problem Definition

Remove the stale `main.py` source-entrypoint assumption from `novaic-app/scripts/sync-vmuse-resource.sh` and make the script validate the current VMuse HTTP contract.

## Proposed Solution

- Replace the script's `src/novaic_mcp_vmuse/main.py` existence check with explicit current-contract validation.
- Prefer concrete source markers that must exist for the committed HTTP-only VMuse package, such as:
  - `src/novaic_mcp_vmuse/http_server.py`
  - `src/novaic_mcp_vmuse/cli.py`
  - `pyproject.toml`
- Do not add compatibility fallbacks for the removed `main.py` path.
- Run or otherwise verify the sync path so both app VMuse bundle copies stay aligned:
  - `novaic-app/src-tauri/resources/novaic-mcp-vmuse`
  - `novaic-app/src-tauri/gen/apple/assets/novaic-mcp-vmuse`

## Verification Plan

- Run `bash -n novaic-app/scripts/sync-vmuse-resource.sh`.
- Run `novaic-app/scripts/sync-vmuse-resource.sh` unless it would create unrelated generated churn; if skipped, document the exact reason and run equivalent focused checks.
- Compare resource and generated VMuse copies after the fix.
- Scan the script for stale `main.py` validation.
- Re-run focused stale VMuse marker scans for active resource/generated paths.

## Acceptance Criteria

- `novaic-app/scripts/sync-vmuse-resource.sh` no longer references `src/novaic_mcp_vmuse/main.py` as its source validation contract.
- The script validates current VMuse HTTP package files.
- Resource and generated VMuse copies remain synchronized with each other.
- No stale FastMCP/SSE/stdio/direct-media active-path residue is introduced.
- The result includes commands and outputs used to verify the fix.
