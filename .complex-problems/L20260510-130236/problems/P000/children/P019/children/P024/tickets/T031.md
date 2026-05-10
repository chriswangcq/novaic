# Ticket: Delete Old Authority Paths And Strengthen Guardrails

## Problem Definition

The active cutover is complete, but old source files, stale docs, and transitional policy allowlists still mention Cortex-owned live file authority and `BlobCortexStore`. This creates exactly the kind of misleading residue the project wants to avoid.

## Proposed Solution

Split cleanup into focused child problems: delete old authority code and update imports/exports, tighten guardrail tests, rewrite final architecture docs, then run full regression and residue scans.

## Acceptance Criteria

- Old Cortex-owned live authority implementation is removed from production source.
- No production import can revive `CortexLogicalFileAuthority` or `BlobCortexStore`.
- Guardrail tests reflect the final LogicalFS/Blob boundary and stop allowing old transitional paths.
- Docs describe Cortex -> LogicalFS -> Blob and Cortex -> sandboxd relationships without old ownership wording.
- Full tests and residue scans pass.

## Verification Plan

- Run targeted guardrail and boundary tests after each cleanup.
- Run full Cortex, LogicalFS, and sandbox-service tests at the end.
- Run repository residue scans for old authority and old constructor patterns.

## Risks

- Removing old exports may break tests that still use `MemoryStore` as a convenient object-store adapter.
- Historical roadmap docs may intentionally mention old names; they must be classified as historical or updated enough not to look canonical.

## Assumptions

- No backwards compatibility branch is required.
- Test helpers may keep `MemoryStore` as an object-store adapter until a later separate rename, but it must not be described as live Cortex file authority.
