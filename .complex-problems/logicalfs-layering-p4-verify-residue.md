# Verify layering refactor and remove misleading residue

## Problem

After extraction and boundary cleanup, verify that active code still works and that no old fallback/duplicate path remains to mislead future maintenance.

## Success Criteria

- Targeted tests pass or any environment skip is explicitly explained.
- Import/compile checks pass.
- Residue scans show no local fallback, command rewrite fallback, or stale duplicate shell path implementations.
- Ledger check records remaining risk honestly.
