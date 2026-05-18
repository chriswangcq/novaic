# Semantic/app/device service residue cleanup and verification

## Problem
Scan cross-service docs/scripts/code for stale or misleading claims that collapse Cortex, Gateway, Business, Device, Queue, Runtime, Blob, LogicalFS, Sandboxd, or display responsibilities. Patch safe active-surface residue and record follow-ups for unsafe broad changes.

## Success Criteria
- Active vs stale/generated/historical references are classified.
- Safe active-surface misleading claims are patched.
- Broad or risky cleanup is split into follow-up problems instead of overreaching.
- Verification includes focused scans and relevant lint/tests for touched files.
