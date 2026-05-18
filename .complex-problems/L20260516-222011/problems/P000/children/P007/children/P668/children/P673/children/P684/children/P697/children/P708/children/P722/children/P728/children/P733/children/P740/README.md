# Classify documentation media-byte residue

## Problem

Classify documentation references to base64, screenshot payloads, display image contracts, Blob artifacts, and VMuse media APIs. Identify stale or misleading docs that can mislead future implementation.

## Success Criteria

- High-signal docs hits are inspected with file pointers.
- Docs are classified as current contract, historical note, stale/misleading, or remediation candidate.
- Exact docs needing edits are listed.
