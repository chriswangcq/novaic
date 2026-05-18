# Clean VMuse source residue and verify resource sync

## Summary

Remove the safe VMuse source residue if confirmed unused, then verify generated app resources remain synchronized.

## Problem Definition

Discovery identified a likely unused `base64` import in `novaic-mcp-vmuse/src/novaic_mcp_vmuse/tools/windows.py`. App resource copies mirror `novaic-mcp-vmuse`; source cleanup must not leave copies stale.

## Proposed Solution

Inspect the source file and import usage. If `base64` is unused, remove it from source. Then run the resource-hygiene check and sync generated copies if the check requires it.

## Acceptance Criteria

- The source import is either removed or explicitly justified as needed.
- Generated VMuse resource copies are synchronized with source or proven unaffected.
- No manual divergent edits are made to generated copies.

## Verification Plan

- Use `rg`/file inspection to verify import usage.
- Run `scripts/ci/test_app_resource_hygiene.py`.
- If necessary, run the established resource sync command and re-run hygiene.
