# Verify Blob boundary cleanup

## Problem

After audit, guardrails, and cleanup, run targeted verification so accepted Blob
uses still work and live `RO` / `RW` bypasses are guarded.

## Success Criteria

- Cortex tests relevant to Blob store/payload/workspace/shell pass.
- Blob-service tests relevant to object/blob APIs pass.
- New guardrails pass and intentionally cover bypass cases.
- Residue scans are recorded with accepted exceptions.
