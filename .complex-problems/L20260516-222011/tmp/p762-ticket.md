# Blob service residue discovery ticket

## Problem Definition

Blob service code may contain stale fallback/local/direct/base64/media wording or old ownership assumptions that conflict with Blob as the durable object/file service.

## Proposed Solution

Scan Blob service source and tests for residue terms, inspect representative hits, and classify them as current object storage behavior, adapter/test fixture, stale remediation candidate, or unrelated vocabulary.

## Acceptance Criteria

- Blob service source and tests are discovered.
- Suspicious hits are classified with file pointers.
- Remediation candidates are listed or absence is recorded.
- No product code is modified.

## Verification Plan

Use `rg --files novaic-blob-service` and focused `rg` searches for fallback/compat/local/direct/base64/media/artifact/blob/storage/legacy terms. Spot-read high-signal files and tests.

## Risks

- Blob is allowed to handle bytes and storage backend details internally; do not treat all binary/base64/storage words as stale.

## Assumptions

- Active Blob service code is under `novaic-blob-service`.
