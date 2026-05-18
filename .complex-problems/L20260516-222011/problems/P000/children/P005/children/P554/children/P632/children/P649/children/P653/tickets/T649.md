# Scan and Classify Live Blob Workspace Authority Paths

## Problem Definition

Live code must not treat Blob as the direct authority for Cortex workspace semantics. We need a code-level scan/classification and concrete fixes/follow-ups for active bypass paths.

## Proposed Solution

Use targeted `rg` scans over live service packages, inspect high-risk files around matches, classify each path, and only edit code if an active Blob-as-workspace semantic bypass is found.

## Acceptance Criteria

- Scan live code packages for Blob/workspace/LogicalFS authority terms.
- Record classification with file pointers.
- Fix or spawn child problem for active semantic bypass.
- Avoid touching valid artifact/display/download Blob usage.

## Verification Plan

Run scans into ledger tmp files. If code changes occur, run focused tests for the affected package. If no code changes occur, record a no-change audit result with evidence.

## Risks

- Blob-related names are broad and can create false positives.
- Some Workspace implementations may legitimately use Blob as byte storage while preserving Workspace semantics.

## Assumptions

- Durable byte storage behind Workspace is allowed; direct ad hoc Blob reads/writes for live `/ro`/`/rw` semantics are not.
