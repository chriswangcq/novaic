# Follow-up: remove stale VMuse main.py assumption from app sync script

## Problem

`novaic-app/scripts/sync-vmuse-resource.sh` still validates the source VMuse repo by checking for `src/novaic_mcp_vmuse/main.py`. The cleaned VMuse package removed that FastMCP-style entrypoint, so the script now encodes an obsolete contract and can block or mislead future app resource/generated synchronization.

## Scope

- Update `novaic-app/scripts/sync-vmuse-resource.sh` so its source validation checks the current HTTP VMuse contract instead of `main.py`.
- Ensure the script continues to sync both:
  - `novaic-app/src-tauri/resources/novaic-mcp-vmuse`
  - `novaic-app/src-tauri/gen/apple/assets/novaic-mcp-vmuse`
- Keep the script free of compatibility fallback branches for removed entrypoints.
- Re-run the sync script or an equivalent focused dry check.
- Verify resource and generated VMuse bundles do not diverge from the source contract.
- Verify no stale `main.py` source validation remains in app VMuse sync paths.

## Success Criteria

- `rg -n "src/novaic_mcp_vmuse/main\\.py|main\\.py" novaic-app/scripts/sync-vmuse-resource.sh` returns no stale validation hit.
- The sync script validates a current source file such as `src/novaic_mcp_vmuse/http_server.py` or another explicit HTTP contract marker.
- Running `novaic-app/scripts/sync-vmuse-resource.sh` succeeds, or an explicit equivalent check proves the same path if running it would cause unrelated generated churn.
- Resource and generated VMuse copies remain synchronized with each other after the fix.
- Focused stale marker scans for FastMCP/SSE/stdio/direct-media residue remain clean outside intentional contract tests.
