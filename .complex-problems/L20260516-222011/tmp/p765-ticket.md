# VMuse service residue discovery ticket

## Problem Definition

VMuse service/MCP code may contain stale direct media exposure, raw screenshot/base64 stdout, fallback/compatibility, or ownership wording that conflicts with the current shell Blob artifact plus display perception boundary.

## Proposed Solution

Scan VMuse source, tests, docs, and scripts for media/base64/artifact/display/Blob residue terms, inspect representative hits, and classify each high-signal group as current lower-level media protocol, shell artifact boundary, stale remediation candidate, or unrelated vocabulary.

## Acceptance Criteria

- VMuse source files are discovered.
- Suspicious hits are classified with file pointers.
- Remediation candidates are listed or absence is recorded.
- No product code is modified in this discovery child.

## Verification Plan

Use `rg --files novaic-mcp-vmuse` and focused `rg` searches for legacy/compat/fallback/direct/bypass/base64/media/artifact/screenshot/display/blob/raw/MCP terms. Spot-read high-signal files and run focused VMuse tests if available.

## Risks

- VMuse lower-level protocols may legitimately handle media bytes, screenshots, and display coordinates. The stale path is active leakage into shell/LLM text, not raw media handling itself.
- The discovery child should not patch product code; remediation belongs to a later remediation branch if candidates are found.

## Assumptions

- Active VMuse code is under `novaic-mcp-vmuse`.
