# Foundational boundary residue cleanup and verification

## Problem

Scan for stale claims that collapse Blob, LogicalFS, or Sandbox responsibilities into Cortex or other higher-level services. Patch safe claims and add/verify guard coverage where appropriate.

## Success Criteria

- Stale boundary claim candidates are listed with evidence and disposition.
- Safe docs/script/comment cleanup is completed; unsafe items are recorded as residual risk.
- Existing or new guard checks cover the important Blob/LogicalFS/Sandbox boundary claims.
- Focused tests/lints pass after any changes.
