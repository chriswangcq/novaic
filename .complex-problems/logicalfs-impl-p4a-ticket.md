# Classify direct Blob and object API usage

## Problem Definition

We need an exact list of direct Blob/object API usages before writing guardrails.
False positives are likely because direct Blob use is allowed for payloads,
attachments, display bytes, artifact bytes, and the transitional storage
adapter.

## Proposed Solution

Run focused scans for `BlobCortexStore`, `/v1/objects`, `/v1/blobs`,
`blob://`, and Blob client classes across Cortex, LogicalFS, sandboxd, runtime,
blob service, app/gateway docs, and tests. Classify each relevant occurrence.

## Acceptance Criteria

- Relevant direct Blob/object usages are listed with source pointers.
- Each usage is classified as allowed, transitional, test-only, stale, or
  blocking.
- Follow-up child problems P007-P009 receive the findings they need.

## Verification Plan

Use `rg`, line-numbered source reads, and a written result.

## Risks

- Large frontend/vendor directories can create noise; keep scans focused.

## Assumptions

- No code changes are expected in this audit ticket.
