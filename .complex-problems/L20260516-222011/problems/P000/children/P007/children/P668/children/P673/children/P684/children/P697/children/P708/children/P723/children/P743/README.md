# Clean VMuse source residue and resource sync

## Summary

Remove safe VMuse source cleanup residue and verify generated app resource copies remain synchronized.

## Problem

`novaic-mcp-vmuse/src/novaic_mcp_vmuse/tools/windows.py` appears to contain an unused `base64` import. Generated app copies mirror the source package and must not be edited by hand.

## Success Criteria

- Confirm whether the `base64` import is unused in source.
- Remove it if unused.
- Run the resource-hygiene check or equivalent sync verification.
- If app generated resource copies become stale, update them through the established sync path rather than manual divergent edits.
