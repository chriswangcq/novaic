# Blob Workspace Authority Residue Audit

## Problem

Blob should remain a cheap artifact/file service, not the authority for live Cortex workspace semantics. Remaining code/docs/tests need classification so Blob-as-workspace authority does not creep back in.

## Success Criteria

- Scans for Blob workspace authority terms and direct blob-backed workspace semantics across Cortex/runtime/common areas.
- Classifies hits as artifact display/download usage, historical docs, tests, or active workspace authority path.
- Removes or creates follow-up for any active Blob-as-workspace authority residue.
