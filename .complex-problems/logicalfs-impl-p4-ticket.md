# Split Blob boundary cleanup into auditable subproblems

## Problem Definition

Direct Blob and object API usage is the riskiest part of the LogicalFS boundary.
Some Blob usage is explicitly allowed for cheap bytes, attachments, payloads,
display bytes, artifact bytes, and LogicalFS persistence internals. Other usage
would be a live `RO` / `RW` bypass. Treating all of this as one execution pass
would hide important boundary distinctions.

## Proposed Solution

Split P004 into smaller child problems:

- Audit all direct Blob/object usage and classify each usage.
- Add guardrails that fail on live `RO` / `RW` Blob bypasses outside the allowed
  authority/storage adapter.
- Clean stale comments/docs/names that imply Blob owns live workspace semantics.
- Verify accepted Blob uses such as payload/audio/display bytes remain intact.

## Acceptance Criteria

- Each direct Blob/object use is classified as allowed cheap-byte use, allowed
  persistence-adapter use, test-only use, or blocking bypass.
- Guardrail tests/scripts fail future direct live `RO` / `RW` Blob bypasses.
- Stale comments/docs implying Blob owns live Workspace semantics are updated.
- Targeted tests pass for Cortex, Blob payload/client paths, and guardrails.

## Verification Plan

Use focused `rg` scans, source inspection, new architecture tests, and targeted
pytest suites. Record all accepted exceptions in result/check bodies.

## Risks

- Over-broad guardrails can block legitimate Blob payload/display/audio use.
- Under-broad guardrails can allow old bypasses to creep back in.

## Assumptions

- `BlobCortexStore` may remain only as a transitional persistence adapter under
  the file authority, not as a Workspace semantic API.
