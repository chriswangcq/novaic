# Audit and tighten LogicalFS RO/RW documentation

## Problem Definition

The current LogicalFS / Blob / Cortex / Sandbox design documents were edited
while the architecture boundary was still being refined. They need to be
audited against the final narrowed principle: LogicalFS owns only Cortex/shell
live `RO` / `RW` semantics; Blob remains the cheap byte/file server for
attachments, display bytes, artifact bytes, and downloads.

## Proposed Solution

Inspect the relevant design/reference documents, scan for over-broad or
contradictory language, patch the docs where needed, and record concrete
evidence that the remaining wording matches the narrowed boundary.

## Acceptance Criteria

- The docs say LogicalFS is the Cortex/shell live `RO` / `RW` authority, not a
  universal file service.
- The docs say Blob is the cheap byte/file server for display/download/artifact
  bytes.
- The docs explicitly say LogicalFS does not expose display/download handles.
- The docs explicitly say RO/RW display/download requires export/copy to Blob.
- Transitional Cortex direct Blob object-store usage is labeled transitional.
- Residue scans do not find conflicting phrases in the audited docs.

## Verification Plan

- Read the relevant docs directly.
- Run focused `rg` scans for broad or conflicting phrases.
- Review the focused diff for the docs touched by this audit.
- Run ledger validation/render/status before final response.

## Risks

- Documentation may still describe desired future behavior rather than current
  code; the audit must distinguish current transitional state from target
  architecture.
- Existing dirty repo state is large; this ticket must not accidentally claim
  unrelated changes.

## Assumptions

- This ticket is documentation-only unless the audit finds a doc/code guard gap
  that must be closed immediately.
- The user's latest clarified boundary is authoritative.
