# Verify base extraction and residue cleanup

## Problem

After extraction and migration, prove that the new base modules are active and no duplicate old paths remain.

## Success Criteria

- `novaic-common` and `novaic-cortex` targeted/full tests pass.
- Residue scans show no duplicate generic process runner, mount namespace helper, or filesystem snapshot implementation in Cortex.
- Ledger records exact remaining risks.
