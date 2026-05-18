# LogicalFS Sandbox Blob Fallback Residue Inventory

## Problem

Search for direct materialization, local fallback, blob-as-real-time-filesystem, and compatibility/backdoor paths that could bypass the intended LogicalFS/sandbox layering. This child belongs under P005 because stale fallback residue is the main risk.

## Success Criteria

- Static scan terms and outputs are recorded.
- Hits are classified as intended, risky, removable, or needing follow-up.
- Any high-confidence risky residue is captured for remediation.
- Blob usage is separated into intended artifact/display usage versus inappropriate RO/RW semantics.
