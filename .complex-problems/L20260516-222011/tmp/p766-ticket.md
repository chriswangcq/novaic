# App resource copy residue discovery ticket

## Problem Definition

App-bundled resource/generated copies may mirror Sandbox or VMuse code and preserve stale imports, direct media behavior, or old entrypoints even after source repos are cleaned.

## Proposed Solution

Discover app resource/generated copies related to VMuse, Sandbox, LogicalFS, and Blob; scan them for residue terms; compare high-signal hits against source-service findings; and list copied cleanup candidates.

## Acceptance Criteria

- Relevant app resource/generated copies are discovered.
- Suspicious hits are classified with file pointers.
- Remediation candidates are listed or absence is recorded.
- No product code is modified in this discovery child.

## Verification Plan

Use `rg --files` and focused `rg` searches under `novaic-app/src-tauri/resources` and `novaic-app/src-tauri/gen/apple/assets` for VMuse/Sandbox/LogicalFS/Blob mirrors and media/base64/FastMCP/direct residue. Spot-read mirrored files that match source-service candidates.

## Risks

- Generated app assets may intentionally mirror source files; discovery should distinguish generated mirror status from source-of-truth remediation responsibility.
- The discovery child should not patch product code; actual source and copied asset cleanup belongs to a later remediation branch.

## Assumptions

- Relevant app resource/generated copies live under `novaic-app/src-tauri/resources` and `novaic-app/src-tauri/gen/apple/assets`.
