# Ticket: Inventory Shell Screenshot BlobRef Manifest Tests

## Problem Definition

Shell-facing screenshot/device commands must return terminal-safe text plus BlobRef artifact metadata, never raw screenshot base64 in stdout/durable text.

## Proposed Solution

Scan shell capability tests for `devicectl`, `tool-output.v1`, runtime artifacts, and base64 absence assertions. Run the focused shell capability test that protects this contract.

## Acceptance Criteria

- Exact scan and focused test commands are recorded.
- Tests proving BlobRef artifact manifest output are cited.
- Tests proving raw base64/data fields are absent from shell-visible output are cited.
- A follow-up is created if direct coverage is missing.

## Verification Plan

Run the focused shell capability Blob contract test file or exact tests covering screenshot output.

## Risks

- Shell output contract may be protected by capability tests rather than runtime tests; cite the owning package clearly.

## Assumptions

- Provider-bound image bytes are outside this shell CLI contract and belong to current display perception, not shell stdout.
